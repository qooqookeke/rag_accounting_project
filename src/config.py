import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# 프로젝트 루트 경로
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    LAW_API_KEY: str = os.getenv("LAW_API_KEY", "")
    
    # LLM Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    
    # Embedding Model Settings
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
    
    # Paths
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = DATA_DIR / "raw"
    PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"
    CHROMA_PERSIST_DIR: Path = Path(os.getenv("CHROMA_PERSIST_DIR", str(DATA_DIR / "chroma_db")))
    
    # RAG Settings
    TOP_K: int = 3
    SIMILARITY_THRESHOLD: float = 0.45

settings = Settings()

# 필요 디렉토리 자동 생성
settings.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
