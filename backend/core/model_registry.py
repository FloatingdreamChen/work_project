from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.config import PROJECT_ROOT, get_settings


@dataclass
class LocalModelStatus:
    name: str
    configured_path: str
    resolved_path: str
    exists: bool
    required_files: list[str]
    missing_files: list[str]
    size_mb: float | None


class LocalModelRegistry:
    """Detect optional local model assets without loading heavy ML libraries."""

    REQUIRED = {
        "bge_m3": ["config.json", "tokenizer.json"],
        "reranker": ["config.json", "tokenizer.json"],
        "classifier": ["config.json", "tokenizer.json"],
        "finetuned_classifier": ["config.json", "tokenizer.json"],
    }

    @classmethod
    def status(cls) -> dict[str, LocalModelStatus]:
        settings = get_settings()
        paths = {
            "bge_m3": settings.bge_m3_model_path,
            "reranker": settings.reranker_model_path,
            "classifier": settings.classifier_model_path,
            "finetuned_classifier": settings.finetuned_classifier_path,
        }
        return {name: cls._status_one(name, path) for name, path in paths.items()}

    @classmethod
    def ready_for_vector_rag(cls) -> bool:
        statuses = cls.status()
        return statuses["bge_m3"].exists and statuses["reranker"].exists

    @classmethod
    def _status_one(cls, name: str, configured_path: str) -> LocalModelStatus:
        resolved = Path(configured_path)
        if not resolved.is_absolute():
            resolved = PROJECT_ROOT / resolved
        required = cls.REQUIRED[name]
        missing = [file_name for file_name in required if not (resolved / file_name).exists()]
        exists = resolved.exists() and not missing
        return LocalModelStatus(
            name=name,
            configured_path=configured_path,
            resolved_path=str(resolved),
            exists=exists,
            required_files=required,
            missing_files=missing,
            size_mb=cls._size_mb(resolved) if resolved.exists() else None,
        )

    @classmethod
    def _size_mb(cls, path: Path) -> float:
        if path.is_file():
            return round(path.stat().st_size / 1024 / 1024, 2)
        total = 0
        for item in path.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
        return round(total / 1024 / 1024, 2)
