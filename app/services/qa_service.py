import os
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

RAG_CHAIN_CACHE = {}

def create_rag_chain(file_path: str, llm_api_key: str, llm_base_url: str, llm_model: str):
    """
    根据给定的文件和模型配置，创建一个完整的 RAG 检索链。
    """
    # 1. 加载文档 (Load)
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()

    # 2. 文档分割 (Split)
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)

    # 3. 嵌入模型 (Embedding)
    # 使用免费的开源模型，它会自动从 HuggingFace 下载
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 4. 存入向量数据库 (Store) & 创建检索器 (Retrieve)
    db = Chroma.from_documents(texts, embeddings)
    retriever = db.as_retriever()

    # 5. 创建 LLM 实例
    llm = ChatOpenAI(
        api_key=SecretStr(llm_api_key), # 使用 SecretStr 包装密钥以符合类型检查
        base_url=llm_base_url,
        model=llm_model
    )

    # 6. 创建 RetrievalQA 链
    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )

    return rag_chain

def query_document(question: str, file_path: str) -> dict:
    """
    对外提供问答服务的主函数。
    它会加载环境变量，创建 RAG 链，并执行查询。
    """
    global RAG_CHAIN_CACHE
    if file_path in RAG_CHAIN_CACHE:
        print(f"使用缓存的 RAG 链，文件路径: {file_path}")
        rag_chain = RAG_CHAIN_CACHE[file_path]
    else:
        print(f"创建新的 RAG 链，文件路径: {file_path}")
        llm_api_key = os.getenv("DEEPSEEK_API_KEY")
        llm_base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        llm_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        if not llm_api_key:
            raise ValueError("DEEPSEEK_API_KEY 环境变量未设置。请在 .env 文件中配置您的 API Key。")

        rag_chain = create_rag_chain(
            file_path=file_path,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            llm_model=llm_model
        )
        RAG_CHAIN_CACHE[file_path] = rag_chain
        

    print(f"正在对问题进行查询: {question}")
    result = rag_chain({"query": question})
    print("查询完成。")

    # 为了方便API返回，我们整理一下结果
    return {
        "answer": result.get("result"),
        "source_documents": [doc.page_content for doc in result.get("source_documents", [])]
    }
    
