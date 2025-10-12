# ingest.py
from pathlib import Path
from app.services.ingestion_service import process_and_embed_document
from app.core.config import settings

def ingest_all_documents():
    """
    遍历 data 目录下的所有 PDF,并调用核心服务进行处理。
    """
    data_dir = Path("data")
    total_splits = 0
    processed_files = 0

    print("开始扫描并处理 data/ 目录下的所有 PDF 文档...")
    # 从 data 目录开始，遍历它自己以及它下面的所有子文件夹，找出所有以 .pdf 结尾的文件
    pdf_files = list(data_dir.rglob("*.pdf"))

    if not pdf_files:
        print("在 data/ 目录下没有找到任何 PDF 文件。")
        return

    for pdf_path in pdf_files:
        print("-" * 50)
        try:
            num_splits = process_and_embed_document(
                file_path=str(pdf_path),
                collection_name=settings.COLLECTION_NAME,
                embeddings_model_name=settings.EMBEDDING_MODEL_NAME,
                connection_string=settings.DATABASE_URL
            )
            if num_splits > 0:
                total_splits += num_splits
                processed_files += 1
        except Exception as e:
            print(f"!!! 处理文件 {pdf_path.name} 时发生未知错误: {e}")

    print("-" * 50)
    print("\n所有文档处理完毕!")
    print(f"总共处理了 {processed_files} 个文件。")
    print(f"总共生成了 {total_splits} 个文本块并存入数据库。")


if __name__ == "__main__":
    ingest_all_documents()