# app/schemas/user.py
from pydantic import BaseModel, Field

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="用户密码")

class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True # 允许从 ORM 模型直接转换

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: str | None = None