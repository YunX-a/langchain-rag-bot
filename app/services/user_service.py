# app/services/user_service.py
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password
from typing import Optional

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    根据用户名从数据库中查询用户。
    """
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, user: UserCreate) -> User:
    """
    创建一个新用户并存入数据库。
    """
    # 使用我们之前创建的安全函数来获取密码的哈希值
    hashed_password = get_password_hash(user.password)

    # 创建 SQLAlchemy 模型实例
    db_user = User(
        username=user.username,
        hashed_password=hashed_password
    )

    # 将新用户添加到数据库会话中
    db.add(db_user)
    # 提交事务，将更改写入数据库
    db.commit()
    # 刷新实例，以获取数据库生成的新 ID 等信息
    db.refresh(db_user)

    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    验证用户名和密码是否正确。
    """
    # 首先，根据用户名查找用户是否存在
    user = get_user_by_username(db, username=username)
    if not user:
        return None # 用户不存在

    # 然后，使用我们创建的安全函数来验证密码是否匹配
    if not verify_password(password, user.hashed_password):
        return None # 密码不正确

    # 验证通过，返回用户对象
    return user

