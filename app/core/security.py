# app/core/security.py
from datetime import datetime, timezone
from jose import jwt
import bcrypt  # <-- 导入新的库
from .config import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services import user_service
from app.schemas.user import TokenData
from app.models.user import User

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否与哈希后的密码匹配"""
    # bcrypt 需要字节串，所以我们对它们进行编码
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    """生成密码的哈希值"""
    # bcrypt 同样需要字节串进行哈希
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    # 将哈希后的字节串解码成字符串以便存入数据库
    return hashed.decode('utf-8')

# ... (create_access_token, oauth2_scheme, get_current_user 等其他函数保持不变) ...

def create_access_token(data: dict) -> str:
    """创建 JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + settings.ACCESS_TOKEN_EXPIRE_DELTA
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY.get_secret_value(), algorithm="HS256")
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    解析并验证 token，返回当前用户。
    如果 token 无效或用户不存在，则会抛出异常。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY.get_secret_value(), algorithms=["HS256"]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    if token_data.username is None:
        raise credentials_exception

    user = user_service.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception

    return user