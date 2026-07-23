from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.router import api_router
from backend.config import get_settings
from backend.core.logger import configure_logging, get_logger


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging("DEBUG" if settings.debug else "INFO")
    logger = get_logger(__name__)
    logger.info("app.starting | env=%s", settings.app_env)
    try:
        from backend.db.migrations import run_migrations

        await run_migrations()
    except Exception as exc:
        logger.warning("app.bootstrap_skipped | error=%s", exc)
    yield
    logger.info("app.shutdown")


app = FastAPI(
    title="考公 AI 助手 API",
    description="岗位匹配、资格风险检查、备考计划、题目解析、申论批改和面试模拟。",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

try:
    from backend.mcp.knowledge_base_server import mcp as kb_mcp
    from backend.mcp.web_search_server import mcp as web_mcp

    if kb_mcp is not None:
        app.mount("/mcp/kb", kb_mcp.streamable_http_app())
    if web_mcp is not None:
        app.mount("/mcp/web-search", web_mcp.streamable_http_app())
except Exception as exc:  # pragma: no cover - startup should survive missing optional MCP deps
    get_logger(__name__).warning("mcp.mount_skipped | error=%s", exc)


@app.get("/health", tags=["系统"])
async def health_check() -> dict:
    return {"status": "ok", "name": settings.app_name, "env": settings.app_env}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.backend_host, port=settings.backend_port)
