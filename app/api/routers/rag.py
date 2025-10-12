# app/api/routers/rag.py
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import tempfile
import os

from app.services import rag_service, ingestion_service
from app.core.config import settings
from app.schemas.rag import QueryRequest, QueryResponse

router = APIRouter()

# 1. 非流式问答接口
@router.post("/query", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    retriever = rag_service.get_retriever(
        connection=settings.DATABASE_URL,
        collection_name=settings.COLLECTION_NAME,
        embeddings_model_name=settings.EMBEDDING_MODEL_NAME
    )
    result = await rag_service.get_answer_from_rag(
        question=request.question,
        retriever=retriever,
        llm_api_key=settings.DEEPSEEK_API_KEY,
        llm_base_url=settings.LLM_BASE_URL,
        llm_model=settings.LLM_MODEL_NAME
    )
    return result

# 2. 流式问答接口
@router.post("/stream-query")
async def stream_ask_question(request: QueryRequest) -> StreamingResponse:
    retriever = rag_service.get_retriever(
        connection=settings.DATABASE_URL,
        collection_name=settings.COLLECTION_NAME,
        embeddings_model_name=settings.EMBEDDING_MODEL_NAME
    )
    answer_generator = rag_service.stream_rag_answer(
        question=request.question,
        retriever=retriever,
        llm_api_key=settings.DEEPSEEK_API_KEY,
        llm_base_url=settings.LLM_BASE_URL,
        llm_model=settings.LLM_MODEL_NAME
    )
    return StreamingResponse(answer_generator, media_type="text/event-stream")

# 3. 文件上传接口
@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="只能上传 PDF 文件。")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        background_tasks.add_task(
            ingestion_service.process_and_embed_document,
            file_path=tmp_path,
            collection_name=settings.COLLECTION_NAME,
            embeddings_model_name=settings.EMBEDDING_MODEL_NAME,
            connection_string=settings.DATABASE_URL
        )
        background_tasks.add_task(os.remove, tmp_path) # 添加任务来清理临时文件

        return {"message": "文件已接收，正在后台处理中...", "filename": file.filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")