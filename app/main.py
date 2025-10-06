from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from pathlib import Path

from .services import qa_service

DEFAULT_MODEL_NAME = "deepseek-chat"
DEFAULT_FILE_PATH = "data/计算机大厂求职面试指南.pdf"

# 加载 .env 文件，这样 qa_service 才能读到 API Key
load_dotenv()

# 创建一个 FastAPI 应用实例
app = FastAPI(
    title="专业级 RAG 问答机器人 API",
    description="一个使用专业工具栈构建的文档问答机器人。",
    version="1.0.0",
)

# 使用 Pydantic 定义 API 的输入数据模型
# 这能确保我们收到的请求数据格式是正确的
class QueryRequest(BaseModel):
    question: str
    file_path: str = "data/计算机大厂求职面试指南.pdf"

# 使用 Pydantic 定义 API 的输出数据模型
# 这能确保我们返回的数据格式是清晰、一致的
class QueryResponse(BaseModel):
    answer: str
    source_documents: list[str]

class ConfigResponse(BaseModel):
    model_name: str
    default_file_path: str
class HealthResponse(BaseModel):
    status: str

class DocsResponse(BaseModel):
    docs: list[str]

# 定义一个 API 端点 (Endpoint)
# @app.post("/query") 的意思是，创建一个接受 POST 请求的 /query 路径
# response_model=QueryResponse 告诉 FastAPI 返回的数据会自动序列化成 QueryResponse 的格式
@app.post("/query", response_model=QueryResponse)
def ask_question(request: QueryRequest):
    """
    接收一个问题，然后调用后端的 RAG 服务来获取答案。
    """
    result = qa_service.query_document(
        question=request.question,
        file_path=request.file_path
    )
    return result

@app.post("/config", response_model=ConfigResponse)
def get_config():
    return {
        "model_name": DEFAULT_MODEL_NAME,
        "default_file_path": DEFAULT_FILE_PATH
    }

@app.post("/health",response_model=HealthResponse)
def get_health():
    return {"status": "ok"}

@app.post("/docs", response_model=DocsResponse)
def query_docs():
    data_dir = Path("data")
    if not data_dir.exists() or not data_dir.is_dir():
        return {"docs": []}

    pdf_files = [str(f.relative_to(data_dir).as_posix()) for f in data_dir.rglob("*.pdf") if f.is_file()]
    return {"docs": pdf_files}
    
# 定义一个根路径，用于快速测试服务是否启动
@app.get("/")
def read_root():
    return {"message": "欢迎使用专业级 RAG 问答机器人 API！"}