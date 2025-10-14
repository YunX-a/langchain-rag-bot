# app/services/rag_service.py (重构后)
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from langchain.chains import RetrievalQA
from langchain_core.vectorstores import VectorStoreRetriever
from app.schemas.rag import SourceDocument
from langchain_core.retrievers import BaseRetriever
import asyncio
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
import json
from sqlalchemy.ext.asyncio import create_async_engine
from typing import Optional
# 缓存 RAG 链或检索器
RETRIEVER_CACHE = {}

def get_retriever(connection: str, collection_name: str, embeddings_model_name: str, async_connection: Optional[str] = None) -> VectorStoreRetriever:
    """
    连接到 PGVector 并返回一个检索器。使用缓存避免重复连接。
    """
    cache_key = f"{connection}:{collection_name}"
    if cache_key in RETRIEVER_CACHE:
        print(f"从缓存中复用检索器 (Key: {cache_key})")
        return RETRIEVER_CACHE[cache_key]

    print(f"首次连接到 PGVector (Collection: {collection_name})")
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

    # 创建 PGVector 实例
    store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=connection,
    )
    
    # 如果提供了异步连接字符串，手动设置异步引擎
    if async_connection:
        async_engine = create_async_engine(async_connection)
        store._async_engine = async_engine
    
    retriever = store.as_retriever()
    RETRIEVER_CACHE[cache_key] = retriever
    return retriever

# --- 创建 RAG 链 ---
def _create_rag_chain(llm: ChatOpenAI, retriever: BaseRetriever):
    """
    统一创建 RAG 链，使用 LangChain Expression Language (LCEL)
    """
    template = """
    仅根据下面提供的上下文来回答问题。如果上下文中没有相关信息，请直接说“根据我所掌握的文档，无法回答这个问题”，不要试图编造答案。
    保持答案简洁明了。
    上下文: {context}
    问题: {input}
    回答:
    """
    prompt = PromptTemplate.from_template(template)

    # 使用 LCEL 的标准方式构建链
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    return rag_chain

# --- 重构后的非流式函数 (变为 async) ---
async def get_answer_from_rag(
    question: str, 
    retriever: BaseRetriever, 
    llm_api_key: SecretStr, 
    llm_base_url: str, 
    llm_model: str
) -> dict:
    """
    (重构后) 异步获取完整的 RAG 答案。
    """
    # 1. 创建 LLM 实例 
    llm = ChatOpenAI(
        api_key=llm_api_key,
        base_url=llm_base_url,
        model=llm_model
    )

    # 2. 调用统一的函数创建 RAG 链
    rag_chain = _create_rag_chain(llm, retriever)

    # 3. 异步调用链
    print(f"正在对问题进行查询: {question}")
    result = await rag_chain.ainvoke({"input": question})
    print("查询完成。")
    
    # 4. 格式化来源文档
    source_documents = [
        SourceDocument(page_content=doc.page_content, metadata=doc.metadata)
        for doc in result.get("context", [])
    ]
    
    return {
        "answer": result.get("answer", ""),
        "source_documents": source_documents
    }

# --- 重构后的流式函数 ---
async def stream_rag_answer(
    question: str,
    retriever: BaseRetriever,
    llm_api_key: SecretStr,
    llm_base_url: str,
    llm_model: str
):
    """
    (重构后) 使用流式响应和异步处理来生成答案。
    """
    print("--- DEBUG 1: 进入 stream_rag_answer 函数 ---")

    print("--- DEBUG 2: 开始检索文档... ---")
    docs = await retriever.ainvoke(question)
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
    
    # 直接复用统一的 RAG 链创建逻辑
    rag_chain = _create_rag_chain(llm, retriever)
    print("--- DEBUG 5: 正在为 RAG 链创建异步任务... ---")
    
    task = asyncio.create_task(
        rag_chain.ainvoke({"input": question})
    )

    try:
        print("--- DEBUG 6: 即将开始遍历回调的 token... ---")
        token_count = 0
        async for token in callback.aiter():
            token_count += 1
            # 我们可以临时打印 token 内容，看看是什么
            # print(f"--- DEBUG 7: 正在 yield token #{token_count}: '{token}' ---")
            yield token
        print(f"--- DEBUG 8: token 遍历结束。共收到 {token_count} 个 token。 ---")
    except Exception as e:
        print(f"--- DEBUG 9: 在流式处理中发生异常: {e} ---")
    finally:
        print("--- DEBUG 10: 进入 finally 块，等待任务完成... ---")
        result = await task
        print("--- DEBUG 11: 任务完成，开始处理来源文档。 ---")
        source_documents = result.get("context", [])

        if source_documents:
            print("--- DEBUG 12: 正在 yield 来源文档。 ---")
            yield "\n\n---SOURCES---\n"
            for doc in source_documents:
                yield json.dumps(doc.metadata) + "\n"
    print("--- DEBUG 13: 退出 stream_rag_answer 函数。 ---")