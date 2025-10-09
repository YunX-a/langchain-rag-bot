# ingest.py
import os
from pathlib import Path
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_postgres import PGVector

# --- 数据库连接信息 ---
CONNECTION_STRING = "postgresql+psycopg2://rag_user:rag_password@localhost:5432/rag_db"
COLLECTION_NAME = "all_documents"

def ingest_documents():
    data_dir = Path("data")
    all_docs = []
    
    print("开始加载所有 PDF 文档...")
    for pdf_path in data_dir.rglob("*.pdf"):
        print(f"  - 正在加载: {pdf_path.name}")
        try: # 增加一个 try...except 块来捕获单个文件的加载错误
            loader = PyMuPDFLoader(str(pdf_path))
            documents = loader.load()
            all_docs.extend(documents)
        except Exception as e:
            print(f"    !!! 加载文件 {pdf_path.name} 时出错: {e}")
    
    if not all_docs:
        print("在 data/ 目录下没有成功加载任何 PDF 文件。")
        return

    print(f"文档加载完成，共 {len(all_docs)} 页。")

    print("开始切分文档...")
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    splits = text_splitter.split_documents(all_docs)
    print(f"文档被切分成 {len(splits)} 个文本块。")

    # --- 核心修改：在这里进行数据清洗 ---
    print("开始清洗文本块中的非法字符...")
    for doc in splits:
        # 将 page_content 中的 NUL(0x00) 字符替换为空字符串
        doc.page_content = doc.page_content.replace('\x00', '')
    print("文本清洗完成。")
    # ------------------------------------

    print("创建嵌入模型...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    print("开始将文档存入 PGVector... (这可能需要很长时间，请耐心等待)")
    PGVector.from_documents(
        embedding=embeddings,
        documents=splits,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
    )
    print("所有文档已成功存入 PGVector 数据库！")


if __name__ == "__main__":
    ingest_documents()