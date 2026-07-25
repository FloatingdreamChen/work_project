from functools import lru_cache
import os
from pathlib import Path

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # pragma: no cover - supports lightweight local tests before deps install
    BaseSettings = object
    SettingsConfigDict = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "GovExamAgent"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 14
    login_max_attempts: int = 5
    login_lock_minutes: int = 15
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    request_concurrency_limit: int = 80
    worker_thread_pool_size: int = 8

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_origin: str = "http://localhost:3000"

    database_url: str = (
        "postgresql+asyncpg://gov_exam:gov_exam_password"
        "@localhost:5434/gov_exam_agent"
    )

    milvus_host: str = "localhost"
    milvus_port: int = 19532
    milvus_collection: str = "gov_exam_knowledge"
    milvus_vector_dim: int = 1024

    openai_api_key: str = ""
    openai_base_url: str = "https://api.deepseek.com/v1"
    openai_model: str = "deepseek-chat"
    openai_fallback_model: str = "deepseek-chat"
    llm_timeout_seconds: float = 20.0
    llm_max_retries: int = 0
    rag_timeout_seconds: float = 3.0

    tavily_api_key: str = ""
    enable_web_search: bool = True
    enable_local_models: bool = False
    enable_milvus_rag: bool = False
    enable_local_semantic_rag: bool = False
    enable_query_classifier: bool = True
    enable_langgraph_checkpoints: bool = False
    graph_memory_backend: str = "memory"
    redis_url: str = "redis://localhost:6379/0"

    bge_m3_model_path: str = "./models/embedding/bge-m3"
    reranker_model_path: str = "./models/reranker/bge-reranker-large"
    classifier_model_path: str = "./models/classifier/all-MiniLM-L6-v2"
    finetuned_classifier_path: str = "./models/classifier/query-classifier-finetuned"

    kb_mcp_server_url: str = "http://localhost:8000/mcp/kb"
    web_search_mcp_url: str = "http://localhost:8000/mcp/web-search"

    jwt_algorithm: str = "HS256"

    if SettingsConfigDict is not None:
        model_config = SettingsConfigDict(
            env_file=(PROJECT_ROOT / ".env", PROJECT_ROOT / ".env.local"),
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )

    def __init__(self, **kwargs):
        if SettingsConfigDict is not None:
            super().__init__(**kwargs)
            return
        for key, default in self.__class__.__dict__.items():
            if key.startswith("_") or callable(default):
                continue
            if key in {"model_config"}:
                continue
            env_value = os.getenv(key.upper())
            value = kwargs.get(key, env_value if env_value is not None else default)
            if isinstance(default, bool) and isinstance(value, str):
                value = value.lower() in {"1", "true", "yes", "on"}
            elif isinstance(default, int) and isinstance(value, str):
                value = int(value)
            elif isinstance(default, float) and isinstance(value, str):
                value = float(value)
            setattr(self, key, value)


@lru_cache
def get_settings() -> Settings:
    return Settings()
