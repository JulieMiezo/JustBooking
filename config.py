import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # MySQL
    DB_HOST: str = "139.162.96.247"
    DB_PORT: int = 30907
    DB_USER: str = "root"
    DB_PASSWORD: str = "e4s276G0uBclUFhQ8g9tLmz3IE5ZT1yj"
    DB_NAME: str = "zeabur"

    # JWT
    SECRET_KEY: str = "change-this-to-a-strong-random-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8小時

    # GCS (Google Cloud Storage) 檔案上傳
    GCS_BUCKET_NAME: Optional[str] = None
    GCS_PROJECT_ID: Optional[str] = None
    # 若用本機儲存，留空即可
    UPLOAD_DIR: str = "uploads"

    # 管理員預設帳號（第一次啟動時建立）
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"  # 正式環境務必修改

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        extra = "ignore"

settings = Settings()
