# LangChain RAG Bot - 智能文档问答系统

基于 LangChain 和 FastAPI 构建的文档问答机器人，支持 PDF 文档的智能检索和问答。

##  功能特性

* **智能文档解析**：支持 PDF 文档的自动解析和文本提取
* **向量化检索**：基于向量相似度的精准文档检索
* **中文优化**：使用 `text2vec-base-chinese` 模型，专为中文文档优化
* **RAG 架构**：完整的检索增强生成 (RAG) 流程实现
* **多种向量存储**：支持 FAISS、PGVector、ChromaDB 等向量数据库
* **用户认证系统**：JWT Token 认证，支持用户注册、登录
* **聊天历史记录**：保存和管理用户的对话历史
* **缓存机制**：内置智能缓存，提升重复查询性能
* **REST API**：基于 FastAPI 的标准化 API 接口
* **CORS 支持**：支持跨域请求，便于前端集成
* **异步处理**：支持异步操作，提升并发性能
* **流式响应**：支持 SSE 流式输出，实时获取 AI 回复

##  技术栈

### 后端核心

* **Web 框架**: FastAPI 0.115.0
* **AI 框架**: LangChain 0.3.27
* **数据校验**: Pydantic 2.12.0
* **异步服务**: Uvicorn

### AI/ML 组件

* **嵌入模型**: HuggingFace (shibing624/text2vec-base-chinese - 中文优化)
* **向量数据库**: FAISS, PGVector, ChromaDB
* **LLM 集成**: OpenAI 兼容接口 (DeepSeek)
* **文档处理**: PyMuPDF, PyPDF

### 开发工具

* **代码质量**: Ruff, Black
* **测试框架**: Pytest
* **环境管理**: Python-dotenv
* **数据库 ORM**: SQLAlchemy 2.0.31
* **数据库**: PostgreSQL + psycopg2
* **身份认证**: JWT (python-jose), bcrypt

##  快速开始

### 1. 环境准备

```bash
git clone https://github.com/YunX-a/langchain-rag-bot.git
cd langchain-rag-bot
```

### 2. 创建虚拟环境

```bash
# 使用 Python 3.11 或更高版本
python -m venv .venv

# Windows 激活
.venv\Scripts\activate

# Linux/Mac 激活
source .venv/bin/activate
```

### 3. 安装依赖

```bash
# 生产环境
pip install -r requirements.txt

# 开发环境（包含额外工具）
pip install -r requirements-dev.txt
```

### 4. 环境配置

创建 `.env` 文件并配置必要的环境变量：

```bash
# 复制示例配置（如果有的话）
cp .env.example .env

# 或者直接创建 .env 文件，添加以下内容：
# DeepSeek API 密钥（必需）
DEEPSEEK_API_KEY=your_api_key_here

# 数据库配置（可选，默认值如下）
DB_USER=rag_user
DB_PASSWORD=rag_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rag_db

# 嵌入模型配置（可选）
EMBEDDING_MODEL_NAME=shibing624/text2vec-base-chinese

# JWT 密钥（生产环境请修改）
SECRET_KEY=your_secret_key_here
```

> 💡 **提示**：首次运行时，嵌入模型会自动从 HuggingFace 下载，可能需要几分钟时间。

### 5. 准备数据

将您的 PDF 文档放入 `data/` 目录：

```bash
mkdir -p data
# 将 PDF 文件复制到 data/ 目录
```

### 6. 启动服务

```bash
# 开发模式（支持热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

服务启动后，访问：

* **API 文档**: <http://localhost:8000/docs>
* **健康检查**: <http://localhost:8000/>
* **API 基础路径**: <http://localhost:8000/api/v1>

## 数据库初始化

如果使用 PostgreSQL 和 PGVector，需要先初始化数据库：

```bash
# 初始化数据库表结构
python db_init.py

# 摄取文档到向量数据库
python ingest.py
```

##  API 使用说明

### 用户认证

#### 注册新用户

```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "password": "your_password",
       "full_name": "张三"
     }'
```

#### 用户登录

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=user@example.com&password=your_password"
```

登录成功后会返回 access_token，后续请求需要在 Header 中携带。

### 查询文档

```bash
curl -X POST "http://localhost:8000/api/v1/rag/query" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -d '{
       "question": "什么是操作系统？"
     }'
```

### 流式查询（SSE）

```bash
curl -X POST "http://localhost:8000/api/v1/rag/query-stream" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -d '{
       "question": "什么是操作系统？"
     }'
```

### 查看聊天历史

```bash
curl -X GET "http://localhost:8000/api/v1/history/" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 响应格式

```json
{
  "answer": "操作系统是管理计算机硬件与软件资源的计算机程序...",
  "source_documents": [
    {
      "page_content": "相关文档片段",
      "metadata": {
        "source": "document.pdf",
        "page": 1
      }
    }
  ]
}
```

### 流式响应格式（SSE）

```text
data: {"type": "token", "content": "操作"}
data: {"type": "token", "content": "系统"}
data: {"type": "token", "content": "是"}
...
data: {"type": "source_documents", "content": [...]}
data: {"type": "done"}
```

##  项目结构

```text
langchain-rag-bot/
├── app/                    # 应用核心代码
│   ├── __init__.py
│   ├── main.py            # FastAPI 应用入口
│   ├── api/               # API 路由层
│   │   ├── deps.py       # 依赖注入
│   │   └── routers/      # 路由模块
│   │       ├── auth.py   # 认证路由
│   │       ├── users.py  # 用户管理
│   │       ├── rag.py    # RAG 问答
│   │       └── history.py # 历史记录
│   ├── core/              # 核心配置
│   │   ├── config.py     # 应用配置
│   │   ├── security.py   # 安全相关
│   │   └── password.py   # 密码处理
│   ├── crud/              # 数据库操作
│   │   ├── crud_user.py  # 用户 CRUD
│   │   └── crud_history.py # 历史记录 CRUD
│   ├── db/                # 数据库连接
│   │   └── session.py    # 数据库会话
│   ├── models/            # 数据库模型
│   │   ├── user.py       # 用户模型
│   │   └── history.py    # 历史记录模型
│   ├── schemas/           # Pydantic 模式
│   │   ├── user.py       # 用户模式
│   │   ├── token.py      # Token 模式
│   │   ├── rag.py        # RAG 模式
│   │   └── history.py    # 历史记录模式
│   └── services/          # 业务逻辑层
│       ├── rag_service.py      # RAG 核心服务
│       ├── user_service.py     # 用户服务
│       └── ingestion_service.py # 文档摄取服务
├── data/                  # PDF 文档存储目录
├── tests/                 # 测试代码
│   ├── __init__.py
│   └── test_qa_service.py
├── frontend/              # 前端代码（可选）
├── .env.example          # 环境变量示例
├── .gitignore
├── requirements.txt       # 生产依赖
├── requirements-dev.txt   # 开发依赖
├── db_init.py            # 数据库初始化脚本
├── ingest.py             # 文档摄取脚本
└── README.md
```

##  配置选项

### 向量数据库配置

项目支持多种向量存储后端：

1. **FAISS**（默认）- 内存存储，适合开发和小规模部署
2. **PGVector** - PostgreSQL 扩展，适合生产环境
3. **ChromaDB** - 轻量级向量数据库

### 嵌入模型配置

支持多种嵌入模型：

* **HuggingFace**：`shibing624/text2vec-base-chinese`（默认，中文优化）
* **备选模型**：`sentence-transformers/all-MiniLM-L6-v2`（多语言）
* **OpenAI**：text-embedding-ada-002
* **自定义模型**：可配置任何兼容的嵌入服务

> 💡 **提示**：默认使用 `shibing624/text2vec-base-chinese` 模型，专为中文文档优化，提供更好的中文检索效果。

##  测试

运行测试套件：

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_qa_service.py

# 生成覆盖率报告
pytest --cov=app tests/
```

##  部署

### Docker 部署

```bash
# 构建镜像
docker build -t langchain-rag-bot .

# 运行容器
docker run -p 8000:8000 --env-file .env langchain-rag-bot
```

### 生产部署建议

1. **使用 PostgreSQL + PGVector** 作为向量数据库
2. **配置反向代理**（Nginx）处理静态文件和负载均衡
3. **启用 HTTPS** 确保 API 安全
4. **设置监控和日志**追踪应用性能
5. **使用容器编排**（Docker Compose/Kubernetes）

##  贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

##  许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

##  注意事项

* 确保有足够的内存来处理大型 PDF 文档
* 首次启动时会自动下载中文嵌入模型（约 400MB），请保持网络畅通
* API 密钥请妥善保管，不要提交到版本控制
* 生产环境建议使用专业的向量数据库（如 PGVector）
* 定期备份重要的文档和配置
* 推荐使用中文文档以获得最佳检索效果

##  支持

如果您遇到问题或有疑问，请：

1. 查看 [Issues](https://github.com/YunX-a/langchain-rag-bot/issues)
2. 创建新的 Issue 描述问题
3. 参考 API 文档：<http://localhost:8000/docs>
