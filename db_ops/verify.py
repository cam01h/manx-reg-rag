"""Checks that a Qdrant collection matches the chunk jsonl files.

`mrr embed` only embeds chunk ids it has not seen, so nothing else notices when
the collection and the jsonl drift apart (a half-finished embed, a deploy that
pulled new jsonl but skipped the embed, a payload refresh that failed, a changed
model or embedding text). Each check returns a list of problems, empty when all
is well. None of them exit or raise, so the app's startup checks and the pytests
can both use them. This module loads no models, so importing it is cheap.

  check_counts    total points against total chunks; on a mismatch, per document
  check_config    vector names, sizes, distance, sparse modifier
  check_indexes   the payload index on sectors (only speeds up filtered searches)
  check_ids       every chunk has a point and every point has a chunk
  check_payloads  every point's payload equals its chunk
  check_vectors   re-embeds a few random chunks and compares with what is stored
"""

import json
import logging
import random
from collections import Counter
from collections.abc import Iterator
from dataclasses import asdict
from typing import Any

import numpy as np
from qdrant_client import QdrantClient, models

from config import DENSE_VECTOR_NAME, SPARSE_VECTOR_NAME
from core.sectors import SECTORS_FIELD
from extraction_ops.models import Chunk

from .utils import (
    build_dense_vector,
    build_embedding_text,
    build_point_id,
    build_sparse_vector,
)

logger = logging.getLogger(__name__)

SCROLL_BATCH = 1000
SHOW_LIMIT = 5
SAMPLE_SIZE = 5
# cosine similarity between a stored vector and a fresh embedding of the same text
MIN_SIMILARITY = 0.999
# stored sparse weights are compared with a small relative tolerance
SPARSE_RTOL = 1e-3


def _all_points(
    client: QdrantClient, collection: str, with_payload: bool = False
) -> Iterator[models.Record]:
    offset = None
    while True:
        records, offset = client.scroll(
            collection_name=collection,
            offset=offset,
            limit=SCROLL_BATCH,
            with_payload=with_payload,
            with_vectors=False,
        )
        yield from records
        if offset is None:
            return


def _expected_payload(chunk: Chunk) -> dict[str, Any]:
    # the payload is stored as asdict(chunk) and comes back as json, so tuples are lists
    return json.loads(json.dumps(asdict(chunk)))


def _count_for_document(client: QdrantClient, collection: str, document: str) -> int:
    return client.count(
        collection_name=collection,
        count_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="document", match=models.MatchValue(value=document)
                )
            ]
        ),
        exact=True,
    ).count


def _list(heading: str, items: list[str], total: int | None = None) -> list[str]:
    total = len(items) if total is None else total
    lines = [f"{heading} [{total}], first {min(SHOW_LIMIT, len(items))}:"]
    lines += [f"    {item}" for item in items[:SHOW_LIMIT]]
    return lines


def check_counts(
    client: QdrantClient, collection: str, chunks: list[Chunk]
) -> list[str]:
    expected = len(chunks)
    found = client.count(collection_name=collection, exact=True).count
    if found == expected:
        return []
    problems = [
        (
            f"collection [{collection}] has [{found}] points but the chunk jsonl "
            f"has [{expected}] chunks"
        )
    ]
    accounted = 0
    for document, wanted in sorted(Counter(c.document for c in chunks).items()):
        got = _count_for_document(client, collection, document)
        accounted += got
        if got != wanted:
            problems.append(f"    [{document}]: jsonl [{wanted}] | qdrant [{got}]")
    if found > accounted:
        problems.append(
            f"    [{found - accounted}] points in qdrant belong to no document in the jsonl"
        )
    return problems


def check_config(client: QdrantClient, collection: str, dense_size: int) -> list[str]:
    info = client.get_collection(collection)
    params = info.config.params
    problems = []

    vectors = params.vectors
    dense = vectors.get(DENSE_VECTOR_NAME) if isinstance(vectors, dict) else None
    if dense is None:
        problems.append(f"no [{DENSE_VECTOR_NAME}] vector configured")
    else:
        if dense.size != dense_size:
            problems.append(
                f"[{DENSE_VECTOR_NAME}] vector size is [{dense.size}], "
                f"the embedding model gives [{dense_size}]"
            )
        if dense.distance != models.Distance.COSINE:
            problems.append(
                f"[{DENSE_VECTOR_NAME}] distance is [{dense.distance}], expected cosine"
            )

    sparse = (params.sparse_vectors or {}).get(SPARSE_VECTOR_NAME)
    if sparse is None:
        problems.append(f"no [{SPARSE_VECTOR_NAME}] sparse vector configured")
    elif sparse.modifier != models.Modifier.IDF:
        problems.append(
            f"[{SPARSE_VECTOR_NAME}] sparse modifier is [{sparse.modifier}], expected idf"
        )

    return problems


def check_indexes(client: QdrantClient, collection: str) -> list[str]:
    info = client.get_collection(collection)
    index = (info.payload_schema or {}).get(SECTORS_FIELD)
    if index is None:
        return [f"no payload index on [{SECTORS_FIELD}]"]
    if index.data_type != models.PayloadSchemaType.KEYWORD:
        return [
            f"payload index on [{SECTORS_FIELD}] is [{index.data_type}], expected keyword"
        ]
    return []


def check_ids(client: QdrantClient, collection: str, chunks: list[Chunk]) -> list[str]:
    expected = {build_point_id(c.chunk_id): c.chunk_id for c in chunks}
    found = {str(record.id) for record in _all_points(client, collection)}
    missing = [expected[i] for i in expected if i not in found]
    extra = [i for i in found if i not in expected]

    problems = []
    if missing:
        problems += _list("in the jsonl but not in qdrant (embed them)", missing)
    if extra:
        # name the extra points by chunk_id where their payload still has one
        records = client.retrieve(
            collection_name=collection,
            ids=extra[:SHOW_LIMIT],
            with_payload=["chunk_id"],
            with_vectors=False,
        )
        names = {str(r.id): (r.payload or {}).get("chunk_id", "?") for r in records}
        labels = [f"{names.get(i, '?')} (point {i})" for i in extra[:SHOW_LIMIT]]
        problems += _list(
            "in qdrant but not in the jsonl (stale)", labels, total=len(extra)
        )
    return problems


def check_payloads(
    client: QdrantClient, collection: str, chunks: list[Chunk]
) -> list[str]:
    expected = {build_point_id(c.chunk_id): _expected_payload(c) for c in chunks}
    differing = []
    for record in _all_points(client, collection, with_payload=True):
        wanted = expected.get(str(record.id))
        if wanted is None:
            continue  # a stale point: check_ids reports it
        actual = record.payload or {}
        if actual != wanted:
            fields = sorted(
                k
                for k in wanted.keys() | actual.keys()
                if wanted.get(k) != actual.get(k)
            )
            differing.append(f"{wanted['chunk_id']} (differs in {', '.join(fields)})")
    if not differing:
        return []
    return _list("payload differs from the jsonl", differing)


def _cosine(a: list[float], b: list[float]) -> float:
    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    return float(x @ y / (np.linalg.norm(x) * np.linalg.norm(y)))


def _sparse_matches(stored: models.SparseVector, fresh: models.SparseVector) -> bool:
    a = dict(zip(stored.indices, stored.values))
    b = dict(zip(fresh.indices, fresh.values))
    if a.keys() != b.keys():
        return False
    return all(np.isclose(a[k], b[k], rtol=SPARSE_RTOL) for k in a)


def check_vectors(
    client: QdrantClient,
    collection: str,
    chunks: list[Chunk],
    dense_model: Any,
    sparse_model: Any,
    sample_size: int = SAMPLE_SIZE,
    seed: int | None = None,
) -> tuple[list[str], int]:
    """Re-embed a random sample and compare with the stored vectors.

    Returns (problems, seed). Pass the seed back in to repeat the same sample.
    This is a canary for a changed model or changed embedding text, which the
    incremental embed would never notice because chunk ids do not change.
    """
    if seed is None:
        seed = random.SystemRandom().randrange(2**32)
    sample = random.Random(seed).sample(chunks, min(sample_size, len(chunks)))
    records = client.retrieve(
        collection_name=collection,
        ids=[build_point_id(c.chunk_id) for c in sample],
        with_payload=False,
        with_vectors=True,
    )
    stored = {str(r.id): r.vector for r in records}

    problems = []
    for chunk in sample:
        vectors = stored.get(build_point_id(chunk.chunk_id))
        if not isinstance(vectors, dict):
            problems.append(f"{chunk.chunk_id}: no vectors in qdrant")
            continue
        text = build_embedding_text(chunk)
        similarity = _cosine(
            vectors[DENSE_VECTOR_NAME], build_dense_vector(text, dense_model)
        )
        if similarity < MIN_SIMILARITY:
            problems.append(
                f"{chunk.chunk_id}: dense vector is stale (similarity {similarity:.4f})"
            )
        if not _sparse_matches(
            vectors[SPARSE_VECTOR_NAME], build_sparse_vector(text, sparse_model)
        ):
            problems.append(f"{chunk.chunk_id}: sparse vector is stale")
    if problems:
        problems.insert(
            0,
            f"re-embedded [{len(sample)}] chunks with seed [{seed}] "
            "(pass the same seed to repeat this sample)",
        )
        problems.append(
            "the model or build_embedding_text changed since these were embedded: "
            "run mrr embed --rebuild"
        )
    return problems, seed
