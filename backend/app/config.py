import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Geospatial File Measurement API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Storage settings
    UPLOAD_DIR: Path = BASE_DIR / "storage" / "uploads"
    ALLOWED_EXTENSIONS: set[str] = {".zip", ".kml"}
    MAX_FILE_SIZE_MB: int = 50
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/geospatial.db"
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    
    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()

# Ensure upload directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
