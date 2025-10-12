# 临时定义 Pydantic 模型，未来会移到 schemas 文件夹
from pydantic import BaseModel, Field
from typing import Optional

# 定义单个来源文档的结构
class SourceDocument(BaseModel):
    page_content: str
    metadata: Optional[dict] = Field(default_factory=dict, description="来源文档的元数据，如页码、来源文件等")

# 定义API的请求体模型
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="用户提出的问题")

# 定义API的响应体模型
class QueryResponse(BaseModel):
    answer: str = Field(..., description="模型生成的答案")
    source_documents: list[SourceDocument] = Field(..., description="答案所参考的来源文档列表")
