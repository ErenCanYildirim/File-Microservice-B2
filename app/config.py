import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./files.db")

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Backblaze B2
    b2_application_key_id: str = os.getenv("B2_APPLICATION_KEY_ID")
    b2_application_key: str = os.getenv("B2_APPLICATION_KEY")
    b2_bucket_name: str = os.getenv("B2_BUCKET_NAME")

    # File upload settings
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: list = [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".pdf",
        ".txt",
        ".doc",
        ".docx",
    ]
    temp_upload_dir: str = "./temp_uploads"

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
