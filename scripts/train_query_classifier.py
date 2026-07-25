"""Fine-tune the local query intent classifier for this project.

The classifier is used for Agent routing only. It does not replace the LLM.
Default paths stay inside the project root.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT_FOR_IMPORT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_FOR_IMPORT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORT))

from backend.config import PROJECT_ROOT, get_settings
from backend.core.query_classifier import INTENT_LABELS
from backend.core.sentence_model_loader import load_sentence_transformer


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Train query intent classifier.")
    parser.add_argument("--train-file", type=Path, default=PROJECT_ROOT / "data" / "training" / "query_intents.jsonl")
    parser.add_argument("--base-model", type=Path, default=PROJECT_ROOT / settings.classifier_model_path)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / settings.finetuned_classifier_path)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--dry-run", action="store_true", help="Validate data and paths without writing model files.")
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        text = str(row.get("text", "")).strip()
        label = str(row.get("label", "")).strip()
        if not text or label not in INTENT_LABELS:
            raise ValueError(f"Invalid row {line_no}: {row}")
        rows.append({"text": text, "label": label})
    return rows


def build_examples(rows: list[dict[str, str]]):
    from sentence_transformers import InputExample

    examples = []
    for row in rows:
        examples.append(InputExample(texts=[row["text"], INTENT_LABELS[row["label"]]], label=1.0))
        for other_label, label_text in INTENT_LABELS.items():
            if other_label != row["label"]:
                examples.append(InputExample(texts=[row["text"], label_text], label=0.0))
    return examples


def main() -> None:
    args = parse_args()
    if not args.train_file.exists():
        raise SystemExit(f"Training file not found: {args.train_file}")
    if not args.base_model.exists():
        raise SystemExit(f"Base model not found: {args.base_model}")
    rows = load_rows(args.train_file)
    label_counts = {label: len([row for row in rows if row["label"] == label]) for label in INTENT_LABELS}
    print(f"loaded_rows={len(rows)}")
    print(f"label_counts={label_counts}")
    print(f"base_model={args.base_model}")
    print(f"output={args.output}")
    if args.dry_run:
        return

    from torch.utils.data import DataLoader
    from sentence_transformers import losses

    model = load_sentence_transformer(args.base_model)
    examples = build_examples(rows)
    train_loader = DataLoader(examples, shuffle=True, batch_size=args.batch_size)
    train_loss = losses.CosineSimilarityLoss(model)
    model.fit(train_objectives=[(train_loader, train_loss)], epochs=args.epochs, show_progress_bar=True)
    args.output.mkdir(parents=True, exist_ok=True)
    model.save(str(args.output))
    print("classifier_training_done=true")


if __name__ == "__main__":
    main()
