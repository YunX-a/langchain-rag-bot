# app/api/routers/rag.py
from fastapi import APIRouter
from app.services import rag_service
from app.core.config import settings
# 导入我们未来将要创建的 Pydantic Schemas
# from app.schemas.rag import QueryRequest, QueryResponse 
from pydantic import BaseModel # 暂时在这里定义

# 临时定义 Pydantic 模型，未来会移到 schemas 文件夹
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    source_documents: list[str]

# 创建一个 API 路由器
router = APIRouter()

@router.post("/query", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    """
    接收一个问题，然后调用后端的 RAG 服务来获取答案。
    """
    # 1. 从配置中心获取检索器
    retriever = rag_service.get_retriever(
        connection=settings.DATABASE_URL,
        collection_name=settings.COLLECTION_NAME,
        embeddings_model_name=settings.EMBEDDING_MODEL_NAME
    )

    # 2. 调用核心服务获取答案
    result = rag_service.get_answer_from_rag(
        question=request.question,
        retriever=retriever,
        llm_api_key=settings.DEEPSEEK_API_KEY,
        llm_base_url=settings.LLM_BASE_URL,
        llm_model=settings.LLM_MODEL_NAME
    )
    return result