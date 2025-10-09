# app/services/qa_service.py (修改后)
import os
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector # <--- 修改点
from langchain.chains import RetrievalQA

# --- 数据库连接信息 ---
CONNECTION_STRING = "postgresql+psycopg2://rag_user:rag_password@localhost:5432/rag_db"
COLLECTION_NAME = "all_documents"

# 缓存现在可以缓存 PGVector 的 store 对象或 retriever 对象
DB_CACHE = {}

def get_retriever():
    """
    连接到 PGVector 并返回一个检索器。使用缓存避免重复连接。
    """
    if "retriever" in DB_CACHE:
        print("从缓存中复用检索器...")
        return DB_CACHE["retriever"]

    print("首次连接到 PGVector 数据库...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


    store = PGVector(
        embeddings=embeddings,  # <-- 修改这里！
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
    )
    retriever = store.as_retriever()
    DB_CACHE["retriever"] = retriever # 存入缓存
    return retriever


def query_document(question: str) -> dict:
    """
    接收问题，使用 PGVector 检索并生成答案。
    """
    # 从 .env 文件加载环境变量
    llm_api_key = os.getenv("DEEPSEEK_API_KEY")
    llm_base_url = "https://api.deepseek.com"
    llm_model = "deepseek-chat"
    if not llm_api_key:
        raise ValueError("错误：未找到 DEEPSEEK_API_KEY。")

    # 1. 获取检索器
    retriever = get_retriever()

    # 2. 创建 LLM
    llm = ChatOpenAI(
        api_key=SecretStr(llm_api_key),
        base_url=llm_base_url,
        model=llm_model
    )

    # 3. 创建 RAG 链
    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    return rag_chain

    print(f"正在对问题进行查询: {question}")
    result = rag_chain({"query": question})
    print("查询完成。")

    return {
        "answer": result.get("result"),
        "source_documents": [doc.page_content for doc in result.get("source_documents", [])]
    }