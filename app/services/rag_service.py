# app/services/rag_service.py (最终修复版 - 同步检索)

from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from langchain_core.vectorstores import VectorStoreRetriever
from app.schemas.rag import SourceDocument
from langchain_core.retrievers import BaseRetriever
import asyncio
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import json
from typing import Optional

# 缓存 RAG 链或检索器
RETRIEVER_CACHE = {}

def get_retriever(connection: str, collection_name: str, embeddings_model_name: str, **kwargs) -> VectorStoreRetriever:
    """
    连接到 PGVector 并返回一个检索器。
    (已简化：移除无效的异步连接逻辑)
    """
    cache_key = f"{connection}:{collection_name}"
    if cache_key in RETRIEVER_CACHE:
        print(f"从缓存中复用检索器 (Key: {cache_key})")
        return RETRIEVER_CACHE[cache_key]

    print(f"首次连接到 PGVector (Collection: {collection_name})")
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

    # 仅使用同步连接创建 store，因为异步路径存在无法解决的问题
    store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=connection,
    )
    
    retriever = store.as_retriever(
        search_kwargs={'k': 10}
    )
    RETRIEVER_CACHE[cache_key] = retriever
    return retriever

# --- 创建 RAG 链 (保持不变) ---
def _create_rag_chain(llm: ChatOpenAI, retriever: BaseRetriever):
    template = """
    仅根据下面提供的上下文来回答问题。如果上下文中没有相关信息，请直接说“根据我所掌握的文档，无法回答这个问题”，不要试图编造答案。
    保持答案简洁明了。
    上下文: {context}
    问题: {input}
    回答:
    """
    prompt = PromptTemplate.from_template(template)
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    return rag_chain

# --- 异步获取答案 (保持不变) ---
async def get_answer_from_rag(
    question: str, 
    retriever: BaseRetriever, 
    llm_api_key: SecretStr, 
    llm_base_url: str, 
    llm_model: str
) -> dict:
    llm = ChatOpenAI(
        api_key=llm_api_key,
        base_url=llm_base_url,
        model=llm_model
    )
    rag_chain = _create_rag_chain(llm, retriever)
    print(f"正在对问题进行查询: {question}")
    result = await rag_chain.ainvoke({"input": question})
    print("查询完成。")
    source_documents = [
        SourceDocument(page_content=doc.page_content, metadata=doc.metadata)
        for doc in result.get("context", [])
    ]
    return {
        "answer": result.get("answer", ""),
        "source_documents": source_documents
    }

# --- 流式获取答案 ---
async def stream_rag_answer(
    question: str,
    retriever: BaseRetriever,
    llm_api_key: SecretStr,
    llm_base_url: str,
    llm_model: str
):
    print("--- DEBUG 1: 进入 stream_rag_answer 函数 ---")
    print("--- DEBUG 2: 开始同步检索文档... ---")
    
    # 使用同步的 invoke 方法替代有问题的 ainvoke
    docs = retriever.invoke(question)
    
    print(f"--- DEBUG 3: 检索到 {len(docs)} 篇文档。 ---")

    if not docs:
        print("--- DEBUG 4: 未找到文档，提前返回。 ---")
        yield "在您的个人知识库和全局知识库中，均未找到与问题相关的文档。请尝试上传文档或更换提问方式。"
        return
    
    callback = AsyncIteratorCallbackHandler()
    llm = ChatOpenAI(
        api_key=llm_api_key, 
        base_url=llm_base_url,
        model=llm_model,
        streaming=True,
        callbacks=[callback],
    )
    
    # 我们需要一个新的 chain 来处理已经检索到的文档
    # 而不是让 chain 再次去检索
    template = """
    仅根据下面提供的上下文来回答问题。如果上下文中没有相关信息，请直接说“根据我所掌握的文档，无法回答这个问题”，不要试图编造答案。
    保持答案简洁明了。
    上下文: {context}
    问题: {input}
    回答:
    """
    prompt = PromptTemplate.from_template(template)
    qa_chain = create_stuff_documents_chain(llm, prompt)
    
    print("--- DEBUG 5: 正在为 QA 链创建异步任务... ---")
    
    # 直接将同步获取的文档和问题传递给问答链
    task = asyncio.create_task(
        qa_chain.ainvoke({"input": question, "context": docs})
    )

    try:
        print("--- DEBUG 6: 即将开始遍历回调的 token... ---")
        async for token in callback.aiter():
            yield token
    except Exception as e:
        print(f"--- DEBUG 9: 在流式处理中发生异常: {e} ---")
    finally:
        print("--- DEBUG 10: 进入 finally 块，等待任务完成... ---")
        # 等待任务完成以确保没有未捕获的异常
        await task
        print("--- DEBUG 11: 任务完成，开始处理来源文档。 ---")

        if docs:
            print("--- DEBUG 12: 正在 yield 来源文档。 ---")
            yield "\n\n---SOURCES---\n"
            for doc in docs:
                yield json.dumps(doc.metadata) + "\n"
    print("--- DEBUG 13: 退出 stream_rag_answer 函数。 ---")