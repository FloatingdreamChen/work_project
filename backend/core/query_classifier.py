from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.config import PROJECT_ROOT, get_settings
from backend.core.model_registry import LocalModelRegistry


INTENT_LABELS = {
    "position_match": "岗位匹配 报名条件 专业限制 资格审核 户籍 基层经历 政治面貌 招录人数 竞争比",
    "study_practice": "备考计划 行测 申论 面试 题目解析 批改 错题 学习报告 模考分数",
}


@dataclass
class QueryClassification:
    intent: str
    confidence: float
    scores: dict[str, float]
    source: str


class QueryClassifier:
    """Local sentence-transformer intent classifier with keyword fallback."""

    _instance: "QueryClassifier | None" = None

    def __init__(self) -> None:
        settings = get_settings()
        model_path = Path(settings.finetuned_classifier_path)
        if not model_path.is_absolute():
            model_path = PROJECT_ROOT / model_path
        if not model_path.exists():
            model_path = PROJECT_ROOT / settings.classifier_model_path
        from backend.core.sentence_model_loader import load_sentence_transformer

        self._model = load_sentence_transformer(model_path)
        self._labels, self._label_embeddings = self._build_label_embeddings()

    @classmethod
    def get_instance(cls) -> "QueryClassifier":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def classify(cls, message: str) -> QueryClassification | None:
        settings = get_settings()
        statuses = LocalModelRegistry.status()
        if not settings.enable_query_classifier:
            return None
        if not (statuses["finetuned_classifier"].exists or statuses["classifier"].exists):
            return None
        try:
            return cls.get_instance()._classify(message)
        except Exception:
            return None

    def _classify(self, message: str) -> QueryClassification:
        query_embedding = self._model.encode([message], normalize_embeddings=True)[0]
        raw_scores: dict[str, float] = {}
        for index, label in enumerate(self._labels):
            raw_scores[label] = float(sum(a * b for a, b in zip(query_embedding, self._label_embeddings[index], strict=False)))
        raw_scores = self._apply_domain_boost(message, raw_scores)
        intent = max(raw_scores, key=raw_scores.get)
        ordered = sorted(raw_scores.values(), reverse=True)
        confidence = ordered[0] - ordered[1] if len(ordered) > 1 else ordered[0]
        return QueryClassification(intent=intent, confidence=round(confidence, 4), scores=raw_scores, source="local_classifier")

    def _apply_domain_boost(self, message: str, scores: dict[str, float]) -> dict[str, float]:
        adjusted = dict(scores)
        position_hits = ("岗位", "职位", "报名", "专业", "资格", "户籍", "基层", "招录", "竞争比")
        practice_hits = ("备考", "计划", "行测", "申论", "面试", "题目", "批改", "错题", "模考")
        adjusted["position_match"] += min(0.16, 0.04 * sum(keyword in message for keyword in position_hits))
        adjusted["study_practice"] += min(0.16, 0.04 * sum(keyword in message for keyword in practice_hits))
        return adjusted

    def _build_label_embeddings(self) -> tuple[list[str], list[list[float]]]:
        training_path = PROJECT_ROOT / "data" / "training" / "query_intents.jsonl"
        examples_by_label: dict[str, list[str]] = {label: [] for label in INTENT_LABELS}
        if training_path.exists():
            import json

            for line in training_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                label = row.get("label")
                text = row.get("text")
                if label in examples_by_label and text:
                    examples_by_label[label].append(str(text))
        labels = list(INTENT_LABELS)
        embeddings: list[list[float]] = []
        for label in labels:
            texts = examples_by_label[label] or [INTENT_LABELS[label]]
            vectors = self._model.encode(texts, normalize_embeddings=True)
            centroid = [sum(float(vector[index]) for vector in vectors) / len(vectors) for index in range(len(vectors[0]))]
            norm = sum(value * value for value in centroid) ** 0.5
            embeddings.append([value / norm for value in centroid] if norm else centroid)
        return labels, embeddings


def classify_query(message: str) -> dict[str, Any] | None:
    result = QueryClassifier.classify(message)
    if result is None:
        return None
    return {
        "intent": result.intent,
        "confidence": result.confidence,
        "scores": result.scores,
        "source": result.source,
    }
