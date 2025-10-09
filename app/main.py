from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
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
    title="RAG 问答机器人",
    description="一个使用专业工具栈构建的文档问答机器人。",
    version="1.0.0",
)

# --- 配置 CORS 中间件 ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源的请求，为了开发方便。生产环境中应设为你的前端域名。
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有 HTTP 请求头
)

# 使用 Pydantic 定义 API 的输入数据模型
# 这能确保我们收到的请求数据格式是正确的
class QueryRequest(BaseModel):
    question: str

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
        question=request.question
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

@app.get("/documents", response_model=DocsResponse)
def list_documents():
    """
    递归扫描 data/ 文件夹及其所有子文件夹，并返回所有 .pdf 文件的相对路径列表。
    """
    data_dir = Path("data")

    if not data_dir.is_dir():
        return {"docs": []}

    # 使用 rglob 进行递归搜索，并返回相对于 data 目录的路径
    pdf_files = [str(f.relative_to(data_dir).as_posix()) for f in data_dir.rglob("*.pdf") if f.is_file()]
    
    # 注意：这里的键名 "docs" 必须和你的 DocsResponse 模型中定义的字段名 "docs" 一致
    return {"docs": pdf_files}
# ------------------------------
    
# 定义一个根路径，用于快速测试服务是否启动
@app.get("/")
def read_root():
    return {"message": "欢迎使用专业级 RAG 问答机器人 API！"}