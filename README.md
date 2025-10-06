# Pro RAG Bot - 专业级文档问答机器人

这是一个使用现代化、专业级工具栈构建的文档问答机器人项目。用户可以通过 API 上传并查询 PDF 文档，实现基于私有知识库的智能问答。

## ✨ 功能特性

* **动态知识库**：支持通过 API 查询不同的 PDF 文档。
* **RAG 核心**：基于 LangChain 实现完整的检索增强生成 (RAG) 流程。
* **高性能**：内置内存缓存机制，对同一文档的多次查询响应迅速。
* **对话历史**：支持多轮对话，能够理解上下文关联。
* **专业 API**：使用 FastAPI 构建，提供清晰、稳定、可交互的后端服务。
* **质量保证**：使用 Pytest 编写单元测试，确保核心逻辑的健壮性。
* **代码规范**：使用 Ruff 进行代码格式化和质量检查。

## 🛠️ 技术栈

* **后端框架**: FastAPI
* **AI 框架**: LangChain
* **数据校验**: Pydantic
* **Python 环境管理**: uv
* **代码质量**: Ruff, pyright
* **测试框架**: pytest
* **向量数据库**: ChromaDB (内存)
* **嵌入模型**: `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face)
* **大语言模型 (LLM)**: DeepSeek (可配置)

## 🚀 快速开始

#### 1. 克隆或下载项目

```bash
git clone [https://github.com/your-username/pro-rag-bot.git](https://github.com/your-username/pro-rag-bot.git)
cd pro-rag-bot
