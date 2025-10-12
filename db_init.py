from app.db.session import engine
from app.models.user import Base # 导入我们定义 User 模型的 Base

def init_db():
    print("正在创建数据库表...")
    # SQLAlchemy 的 metadata 会找到所有继承自 Base 的类，并在数据库中创建对应的表
    Base.metadata.create_all(bind=engine)
    print("数据库表创建成功！")

if __name__ == "__main__":
    init_db()