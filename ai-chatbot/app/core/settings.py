import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def _get_str(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip()


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        print(f"[경고] 환경변수 {name} 값이 정수가 아닙니다. 기본값 {default} 사용")
        return default


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        print(f"[경고] 환경변수 {name} 값이 실수가 아닙니다. 기본값 {default} 사용")
        return default


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "y", "on")


class Settings:
    APP_NAME: str = _get_str("APP_NAME", "AI Chatbot")
    APP_ENV: str = _get_str("APP_ENV", "local")

    POSTGRES_HOST: str = _get_str("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = _get_int("POSTGRES_PORT", 5432)
    POSTGRES_DB: str = _get_str("POSTGRES_DB", "chatbot")
    POSTGRES_USER: str = _get_str("POSTGRES_USER", "chatbot_user")
    POSTGRES_PASSWORD: str = _get_str("POSTGRES_PASSWORD", "chatbot_pass")

    ELASTICSEARCH_HOST: str = _get_str("ELASTICSEARCH_HOST", "http://localhost:9200")

    OPENAI_API_KEY: str = _get_str("OPENAI_API_KEY", "")
    OPENAI_CHAT_MODEL: str = _get_str("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
    OPENAI_EMBEDDING_MODEL: str = _get_str("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    OPENAI_VISION_MODEL: str = _get_str("OPENAI_VISION_MODEL", "gpt-4.1-mini")

    VISION_ENABLED: bool = _get_bool("VISION_ENABLED", True)
    VISION_PROVIDER: str = _get_str("VISION_PROVIDER", "openai")
    VISION_MAX_IMAGE_SIZE_MB: int = _get_int("VISION_MAX_IMAGE_SIZE_MB", 10)

    LLM_PROVIDER: str = _get_str("LLM_PROVIDER", "openai")
    PRIMARY_LLM_PROVIDER: str = _get_str("PRIMARY_LLM_PROVIDER", "ollama")
    FALLBACK_LLM_PROVIDER: str = _get_str("FALLBACK_LLM_PROVIDER", "openai")
    LLM_AUTO_SWITCH_MAX_CHARS: int = _get_int("LLM_AUTO_SWITCH_MAX_CHARS", 600)

    OLLAMA_BASE_URL: str = _get_str("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = _get_str("OLLAMA_MODEL", "llama3.2")
    LLM_TIMEOUT: int = _get_int("LLM_TIMEOUT", 180)

    OLLAMA_TEMPERATURE: float = _get_float("OLLAMA_TEMPERATURE", 0.1)
    OLLAMA_TOP_P: float = _get_float("OLLAMA_TOP_P", 0.8)
    OLLAMA_NUM_PREDICT: int = _get_int("OLLAMA_NUM_PREDICT", 512)
    OLLAMA_REPEAT_PENALTY: float = _get_float("OLLAMA_REPEAT_PENALTY", 1.1)

    EMBEDDING_PROVIDER: str = _get_str("EMBEDDING_PROVIDER", "bge")
    BGE_MODEL_NAME: str = _get_str("BGE_MODEL_NAME", "BAAI/bge-m3")

    CHUNK_SIZE: int = _get_int("CHUNK_SIZE", 300)
    CHUNK_OVERLAP: int = _get_int("CHUNK_OVERLAP", 50)

    TOP_K_RETRIEVAL: int = _get_int("TOP_K_RETRIEVAL", 10)
    TOP_N_CONTEXT: int = _get_int("TOP_N_CONTEXT", 3)

    RAW_DOCS_DIR: str = _get_str("RAW_DOCS_DIR", "data/raw_docs")

    RRF_K: int = _get_int("RRF_K", 60)
    HYBRID_VECTOR_WEIGHT: float = _get_float("HYBRID_VECTOR_WEIGHT", 1.0)
    HYBRID_KEYWORD_WEIGHT: float = _get_float("HYBRID_KEYWORD_WEIGHT", 1.0)

    RERANKER_MODEL: str = _get_str("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    TOP_N_RERANK: int = _get_int("TOP_N_RERANK", 3)

    EMBEDDING_BATCH_SIZE: int = _get_int("EMBEDDING_BATCH_SIZE", 32)
    PG_INSERT_BATCH_SIZE: int = _get_int("PG_INSERT_BATCH_SIZE", 100)
    ES_BULK_BATCH_SIZE: int = _get_int("ES_BULK_BATCH_SIZE", 200)

    OCR_ENABLED: bool = _get_bool("OCR_ENABLED", True)
    OCR_LANG_LIST: str = _get_str("OCR_LANG_LIST", "ko,en")
    OCR_MIN_TEXT_LENGTH: int = _get_int("OCR_MIN_TEXT_LENGTH", 80)
    OCR_RENDER_DPI: int = _get_int("OCR_RENDER_DPI", 200)

    APP_SQLITE_PATH: str = _get_str("APP_SQLITE_PATH", "data/app_state.db")
    SESSION_UPLOAD_DIR: str = _get_str("SESSION_UPLOAD_DIR", "data/uploads/session")
    MANAGED_UPLOAD_DIR: str = _get_str("MANAGED_UPLOAD_DIR", "data/uploads/managed")
    SESSION_FILE_TTL_DAYS: int = _get_int("SESSION_FILE_TTL_DAYS", 7)
    MAX_UPLOAD_FILE_SIZE_MB: int = _get_int("MAX_UPLOAD_FILE_SIZE_MB", 50)

    JWT_SECRET_KEY: str = _get_str("JWT_SECRET_KEY", "dev-secret-key-change-me")
    JWT_ALGORITHM: str = _get_str("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = _get_int("JWT_EXPIRE_MINUTES", 1440)


settings = Settings()