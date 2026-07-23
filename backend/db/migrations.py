from pathlib import Path

from sqlalchemy import text

from backend.core.logger import get_logger
from backend.db.session import AsyncSessionLocal


logger = get_logger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


async def run_migrations() -> None:
    """Apply the idempotent bootstrap SQL used by docker-compose."""
    sql_path = PROJECT_ROOT / "scripts" / "init_db.sql"
    if not sql_path.exists():
        logger.warning("db.init_sql_missing")
        return

    statements = [
        statement.strip()
        for statement in sql_path.read_text(encoding="utf-8").split(";")
        if statement.strip()
    ]
    async with AsyncSessionLocal() as session:
        try:
            for statement in statements:
                await session.execute(text(statement))
            await session.commit()
            logger.info("db.migrations_done")
        except Exception as exc:
            await session.rollback()
            logger.warning("db.migrations_failed | error=%s", exc)
