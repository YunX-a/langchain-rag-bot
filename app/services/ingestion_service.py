# app/services/ingestion_service.py
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector
from typing import List
import tempfile
import os
from ..core.config import settings # 导入配置

def process_and_embed_document(file_path: str, collection_name: str, embeddings_model_name: str, connection_string: str):
    """
    加载、处理单个 PDF 文档，并将其嵌入到向量数据库中。
    这是一个可复用的核心函数。
    """
    print(f"开始处理文件: {file_path}")

    # 1. 加载文档
    try:
        loader = PyMuPDFLoader(file_path)
        documents = loader.load()
    except Exception as e:
        print(f"加载文件 {file_path} 时出错: {e}")
        return 0 # 返回处理失败

    # 2. 切分文档
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(documents)

    if not splits:
        print(f"文件 {file_path} 未能切分出任何文本块。")
        return 0

    print(f"文件被切分成 {len(splits)} 个文本块。")

    # 3. 清洗文本
    for doc in splits:
        doc.page_content = doc.page_content.replace('\x00', '')

    # 4. 创建嵌入模型
    embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)

    # 5. 存入 PGVector
    PGVector.from_documents(
        embedding=embeddings,
        documents=splits,
        collection_name=collection_name,
        connection=connection_string,
    )

    print(f"文件 {file_path} 已成功存入数据库。")
    return len(splits) # 返回成功处理的文本块数量