# app/api/routers/rag.py
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse

from langchain.retrievers import MergerRetriever

from typing import AsyncGenerator
import tempfile
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends

from app.services import rag_service, ingestion_service
from app.core.config import settings
from app.schemas.rag import QueryRequest, QueryResponse

from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

def get_user_collection_name(user: User) -> str:
    """根据用户ID生成专属的集合名称"""
    return f"user_{user.id}_collection"

# 1. 非流式问答接口
@router.post("/query", response_model=QueryResponse)
async def ask_question(request: QueryRequest, current_user: User = Depends(get_current_user)):
    user_collection_name = get_user_collection_name(current_user)

    # 1. 获取用户个人检索器
    user_retriever = rag_service.get_retriever(
        connection=settings.DATABASE_URL,
        collection_name=user_collection_name,
        embeddings_model_name=settings.EMBEDDING_MODEL_NAME,
        async_connection=settings.ASYNC_DATABASE_URL
    )
    global_retriever = rag_service.get_retriever(
        connection=settings.DATABASE_URL,
        collection_name=settings.COLLECTION_NAME,
        embeddings_model_name=settings.EMBEDDING_MODEL_NAME,
        async_connection=settings.ASYNC_DATABASE_URL
    )

    # 3. 合并两个检索器
    combined_retriever = MergerRetriever(retrievers=[user_retriever, global_retriever])
    # --- 修改结束 ---

    result = await rag_service.get_answer_from_rag(
        question=request.question,
        retriever=combined_retriever, # 传递合并后的检索器
        llm_api_key=settings.DEEPSEEK_API_KEY,
        llm_base_url=settings.LLM_BASE_URL,
        llm_model=settings.LLM_MODEL_NAME
    )
    return result

# 2. 流式问答接口
@router.post("/stream-query")
async def stream_ask_question(request: QueryRequest, current_user: User = Depends(get_current_user)) -> StreamingResponse:
    user_collection_name = get_user_collection_name(current_user)

    user_retriever = rag_service.get_retriever(
        connection=settings.DATABASE_URL,
        collection_name=user_collection_name,
        embeddings_model_name=settings.EMBEDDING_MODEL_NAME,
        async_connection=settings.ASYNC_DATABASE_URL
    )
    global_retriever = rag_service.get_retriever(
        connection=settings.DATABASE_URL,
        collection_name=settings.COLLECTION_NAME,
        embeddings_model_name=settings.EMBEDDING_MODEL_NAME,
        async_connection=settings.ASYNC_DATABASE_URL
    )

    # 3. 合并两个检索器
    combined_retriever = MergerRetriever(retrievers=[user_retriever, global_retriever])
    # --- 修改结束 ---

    answer_generator = rag_service.stream_rag_answer(
        question=request.question,
        retriever=combined_retriever, # 传递合并后的检索器
        llm_api_key=settings.DEEPSEEK_API_KEY,
        llm_base_url=settings.LLM_BASE_URL,
        llm_model=settings.LLM_MODEL_NAME
    )
    return StreamingResponse(answer_generator, media_type="text/event-stream")
# 3. 文件上传接口
@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="只能上传 PDF 文件。")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        collection_name = get_user_collection_name(current_user)
        background_tasks.add_task(
            ingestion_service.process_and_embed_document,
            file_path=tmp_path,
            collection_name=collection_name, # 使用用户专属集合
            embeddings_model_name=settings.EMBEDDING_MODEL_NAME,
            connection_string=settings.DATABASE_URL
        )
        
        background_tasks.add_task(os.remove, tmp_path) # 添加任务来清理临时文件

        return {"message": "文件已接收，正在后台处理中...", "filename": file.filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")