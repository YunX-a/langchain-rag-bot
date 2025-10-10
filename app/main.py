from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import rag  # 导入我们新的 RAG 路由

# 创建 FastAPI 应用实例
app = FastAPI(
    title="专业级 RAG 问答机器人 API",
    description="一个使用专业工具栈构建的文档问答机器人。",
    version="1.0.0",
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含 (挂载) RAG 相关的 API 路由
# 所有在 rag.py 中定义的 API 都会被自动添加进来
app.include_router(rag.router, prefix="/api/v1", tags=["RAG"])

# 定义一个根路径，用于快速测试服务是否启动
@app.get("/")
def read_root():
    return {"message": "欢迎使用专业级 RAG 问答机器人 API！"}