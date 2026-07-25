from __future__ import annotations

from pathlib import Path


def load_sentence_transformer(model_path: str | Path):
    """Load SentenceTransformer from either SBERT or plain HF transformer layout."""
    from sentence_transformers import SentenceTransformer, models

    path = Path(model_path)
    if (path / "modules.json").exists():
        try:
            return SentenceTransformer(str(path))
        except Exception:
            pass
    transformer = models.Transformer(str(path), max_seq_length=512)
    pooling = models.Pooling(
        transformer.get_word_embedding_dimension(),
        pooling_mode_mean_tokens=True,
    )
    return SentenceTransformer(modules=[transformer, pooling])
