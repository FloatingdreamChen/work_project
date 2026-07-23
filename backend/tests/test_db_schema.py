from pathlib import Path

from backend.db.migrations import split_sql_statements


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_split_sql_statements_ignores_empty_segments() -> None:
    assert split_sql_statements("CREATE TABLE a(); ;\nCREATE INDEX b ON a(id);") == [
        "CREATE TABLE a()",
        "CREATE INDEX b ON a(id)",
    ]


def test_init_db_contains_audit_and_search_indexes() -> None:
    sql = (PROJECT_ROOT / "scripts" / "init_db.sql").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS position_import_audits" in sql
    assert "CREATE TABLE IF NOT EXISTS current_information_sources" in sql
    assert "idx_current_sources_published" in sql
    assert "idx_practice_metrics_user_module" in sql
    assert "idx_knowledge_chunks_document" in sql
