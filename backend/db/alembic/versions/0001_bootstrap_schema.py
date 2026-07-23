from __future__ import annotations

from pathlib import Path

from alembic import op


revision = "0001_bootstrap_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql_path = Path(__file__).resolve().parents[4] / "scripts" / "init_db.sql"
    for statement in sql_path.read_text(encoding="utf-8").split(";"):
        statement = statement.strip()
        if statement:
            op.execute(statement)


def downgrade() -> None:
    # Initial bootstrap is intentionally not destructive.
    pass
