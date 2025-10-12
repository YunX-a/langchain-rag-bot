from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 使用我们 config.py 中的数据库连接字符串
engine = create_engine(settings.DATABASE_URL)

# 创建一个 SessionLocal 类，它的实例将是实际的数据库会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    FastAPI 依赖项，用于获取数据库会话。
    确保每个请求都使用独立的会话，并在结束后关闭它。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()