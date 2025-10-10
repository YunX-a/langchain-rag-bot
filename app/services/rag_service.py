# app/services/rag_service.py (重构后)
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from langchain.chains import RetrievalQA
from langchain_core.vectorstores import VectorStoreRetriever

# 缓存 RAG 链或检索器
RETRIEVER_CACHE = {}

def get_retriever(connection: str, collection_name: str, embeddings_model_name: str) -> VectorStoreRetriever:
    """
    连接到 PGVector 并返回一个检索器。使用缓存避免重复连接。
    """
    cache_key = f"{connection}:{collection_name}"
    if cache_key in RETRIEVER_CACHE:
        print(f"从缓存中复用检索器 (Key: {cache_key})")
        return RETRIEVER_CACHE[cache_key]

    print(f"首次连接到 PGVector (Collection: {collection_name})")
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

    store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=connection,
    )
    retriever = store.as_retriever()
    RETRIEVER_CACHE[cache_key] = retriever
    return retriever

def get_answer_from_rag(
    question: str, 
    retriever: VectorStoreRetriever, 
    llm_api_key: SecretStr, 
    llm_base_url: str, 
    llm_model: str
) -> dict:
    """
    接收问题和已创建的检索器，生成答案。
    """
    llm = ChatOpenAI(
        api_key=llm_api_key.get_secret_value(), # 从 SecretStr 中获取真实值
        base_url=llm_base_url,
        model=llm_model
    )

    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )

    print(f"正在对问题进行查询: {question}")
    result = rag_chain.invoke({"query": question}) # 使用 invoke
    print("查询完成。")

    return {
        "answer": result.get("result"),
        "source_documents": [doc.page_content for doc in result.get("source_documents", [])]
    }