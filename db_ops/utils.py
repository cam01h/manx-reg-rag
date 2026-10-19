import logging
import uuid
from pathlib import Path
from typing import Any

from fastembed import SparseTextEmbedding, TextEmbedding
from pydantic import TypeAdapter, ValidationError
from qdrant_client import models

logger = logging.getLogger(__name__)


def load_jsonl_dir(path: Path, model: type) -> list[Any]:
    jsonl_files = sorted(path.glob("*.jsonl"))
    if not jsonl_files:
        logger.error("no jsonl file found at [%s]", path)
        raise FileNotFoundError(f"no jsonl files found at [{path}]")
    objects = []
    adapter = TypeAdapter(model)
    for f in jsonl_files:
        try:
            lines = f.read_text().splitlines()
            objects.extend(
                adapter.validate_json(line) for line in lines if line.strip()
            )
        except (OSError, ValidationError):
            logger.exception("failed to load/validate objects in [%s]", f)
            raise
    return objects


def build_point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def build_dense_vector(text: str, model: TextEmbedding) -> list[float]:
    return next(iter(model.embed([text]))).tolist()


def build_sparse_vector(text: str, model: SparseTextEmbedding) -> models.SparseVector:
    emb = next(iter(model.embed([text])))
    vector = models.SparseVector(
        indices=emb.indices.tolist(),
        values=emb.values.tolist(),
    )
    return vector
