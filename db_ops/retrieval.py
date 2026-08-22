import json
from pathlib import Path
from functools import lru_cache
from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient, models
from config import (
    COLLECTION,
    DEFAULT_CHUNKS_RETRIEVED,
    DEFINITIONS_JSONL_PATH,
    DENSE_VECTOR_NAME,
    RETRIEVAL_MODE,
    SPARSE_VECTOR_NAME,
)
from db_ops.models import DefinitionRecord, Payload
from pydantic_ai import RunContext
from app.deps import AppDeps
import logging

logger = logging.getLogger(__name__)


# fastembed used directly to avoid concurecy issues in qudrant client
def embed_query_dense(text: str, model: TextEmbedding) -> list[float]:
    return list(model.embed([text]))[0].tolist()


def embed_query_sparse(text: str, model: SparseTextEmbedding) -> models.SparseVector:
    vector = list(model.embed([text]))[0]
    return models.SparseVector(
        indices=vector.indices.tolist(),
        values=vector.values.tolist(),
    )


def query_dense(client, collection, dense_vec, top_n):
    return client.query_points(
        collection_name=collection,
        query=dense_vec,
        using=DENSE_VECTOR_NAME,
        limit=top_n,
    )


def query_sparse(client, collection, sparse_vec, top_n):
    return client.query_points(
        collection_name=collection,
        query=sparse_vec,
        using=SPARSE_VECTOR_NAME,
        limit=top_n,
    )


def query_hybrid(client, collection, dense_vec, sparse_vec, top_n):
    return client.query_points(
        collection_name=collection,
        prefetch=[
            models.Prefetch(query=dense_vec, using=DENSE_VECTOR_NAME, limit=top_n),
            models.Prefetch(query=sparse_vec, using=SPARSE_VECTOR_NAME, limit=top_n),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=top_n,
    )


# results isnt typed as pyright is having a conflict
def query_collection(
    dense_vec: list[float],
    sparse_vec: models.SparseVector,
    client: QdrantClient,
    collection: str = COLLECTION,
    top_n: int = DEFAULT_CHUNKS_RETRIEVED,
    mode: str = RETRIEVAL_MODE,
):
    try:
        if mode == "dense":
            results = query_dense(client, collection, dense_vec, top_n)
        elif mode == "sparse":
            results = query_sparse(client, collection, sparse_vec, top_n)
        elif mode == "hybrid":
            results = query_hybrid(client, collection, dense_vec, sparse_vec, top_n)
        else:
            logger.critical("unknown retrieval mode [%s]", mode)
            raise ValueError(f"unknown retrieval mode: [{mode}]")
    except Exception:
        logger.exception("failed connection to qdrant")
        raise
    if not results.points:
        logger.critical("no results found from query")
    return results


def return_payload(results) -> list[Payload]:
    chunks = [
        Payload(**r.payload, score=r.score, rank=i + 1)
        for i, r in enumerate(results.points)
    ]
    logger.info("[%d] chunks returned:", len(chunks))
    for c in chunks:
        logger.info("[%s]", c.headers)
    return chunks


@lru_cache(maxsize=1)
def load_definitions(
    path: Path = DEFINITIONS_JSONL_PATH,
) -> tuple[DefinitionRecord, ...]:
    if not path.exists():
        logger.critical("no definitions jsonl file found at [%s]", path)
        raise FileNotFoundError(f"no definitions jsonl file found at [{path}]")
    try:
        definitions = tuple(
            DefinitionRecord(**json.loads(line))
            for line in path.read_text().splitlines()
        )
    except (json.JSONDecodeError, TypeError):
        logger.exception("failed to read to [%s]", path)
        raise
    return definitions


def match_definitions(
    chunks: list[Payload], definitions: tuple[DefinitionRecord, ...]
) -> set[DefinitionRecord]:
    # pyright bug: reportUnhashable false positive on BaseModel subclasses with
    # explicit __hash__, verified correct at runtime — github.com/microsoft/pyright/issues/9249
    matched_definitions = {
        d
        for d in definitions
        if any(
            d.document == c.document and d.term in (c.terms_used or []) for c in chunks
        )  # pyright: ignore[reportUnhashable]
    }

    requested = {(c.document, term) for c in chunks for term in (c.terms_used or [])}
    found = {(d.document, d.term) for d in matched_definitions}
    missing = requested - found

    if missing:
        logger.warning(
            "no definition found for [%d] terms: [%s]", len(missing), missing
        )

    return matched_definitions


def get_chunks_with_definitions(
    ctx: RunContext[AppDeps],
    query: str,
) -> tuple[list[Payload], list[DefinitionRecord]]:
    """Search the Isle of Man AML legislation and guidance for content relevant to the query.
    Returns the most relevant sections from the regulations and any defined terms used in them."""
    logger.info("qdrant queried using search phrase: [%s]", query)
    dense_vector = embed_query_dense(query, ctx.deps.dense_model)
    sparse_vector = embed_query_sparse(query, ctx.deps.sparse_model)
    results = query_collection(dense_vector, sparse_vector, ctx.deps.qdrant_client)
    chunks = return_payload(results)
    definitions_data = load_definitions()
    definitions = match_definitions(chunks, definitions_data)
    return chunks, sorted(definitions, key=lambda d: (d.document, d.term))
