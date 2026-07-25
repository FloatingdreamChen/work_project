from pathlib import Path

from backend.core.query_classifier import INTENT_LABELS
from backend.core.query_classifier import QueryClassifier
from scripts.train_query_classifier import load_rows


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_query_classifier_training_data_is_valid() -> None:
    rows = load_rows(PROJECT_ROOT / "data" / "training" / "query_intents.jsonl")
    labels = {row["label"] for row in rows}

    assert labels == set(INTENT_LABELS)
    assert len(rows) >= 10


def test_query_classifier_domain_boost_corrects_close_scores() -> None:
    classifier = QueryClassifier.__new__(QueryClassifier)

    scores = classifier._apply_domain_boost(
        "我计算机专业可以报哪些深圳岗位",
        {"position_match": 0.69, "study_practice": 0.70},
    )

    assert scores["position_match"] > scores["study_practice"]
