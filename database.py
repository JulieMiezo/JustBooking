import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# MySQL 連線字串
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    f"?charset=utf8mb4"
)

# 如果同資料夾有 server-ca.pem,就啟用 SSL 連線(Cloud SQL 若設定「僅允許 SSL 連線」需要這個)
connect_args = {}
_ca_path = os.path.join(os.path.dirname(__file__), "server-ca.pem")
if os.path.exists(_ca_path):
    # check_hostname=False:Cloud SQL 憑證是綁 instance 名稱,不是綁公開 IP,關掉才不會驗證失敗
    connect_args["ssl"] = {"ca": _ca_path, "check_hostname": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,       # 自動重連
    pool_recycle=3600,        # 每小時回收連線
    pool_size=10,
    max_overflow=20,
    echo=False,               # 正式環境關閉 SQL log,debug 改 True
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
