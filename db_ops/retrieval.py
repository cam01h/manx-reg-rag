import json
from pathlib import Path
from functools import lru_cache
from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient, models
from config import (
    COLLECTION,
    DEFINITIONS_JSONL_PATH,
    DENSE_VECTOR_NAME,
    FINAL_RETURN_TOP_N,
    LEGISLATION_QUOTA_RATIO,
    PRE_RERANK_POOL,
    RETRIEVAL_MODE,
    SPARSE_VECTOR_NAME,
    USE_RERANKER,
)
from db_ops.models import DefinitionRecord, Payload
from pydantic_ai import RunContext
from app.deps import AppDeps
import logging
import uuid

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


def build_exclusion_filter(seen_ids: set[str]) -> models.Filter | None:
    if not seen_ids:
        return None
    point_ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, cid)) for cid in seen_ids]
    logger.info("excluding [%d] previously returned chunks", len(point_ids))
    return models.Filter(must_not=[models.HasIdCondition(has_id=point_ids)])  # pyright: ignore[reportArgumentType]


def query_dense(
    client: QdrantClient,
    collection: str,
    dense_vec: list[float],
    seen: set[str],
    top_n: int = PRE_RERANK_POOL,
):
    return client.query_points(
        collection_name=collection,
        query=dense_vec,
        using=DENSE_VECTOR_NAME,
        limit=top_n,
        query_filter=build_exclusion_filter(seen),
    )


def query_sparse(
    client: QdrantClient,
    collection: str,
    sparse_vec: models.SparseVector,
    seen: set[str],
    top_n: int = PRE_RERANK_POOL,
):
    return client.query_points(
        collection_name=collection,
        query=sparse_vec,
        using=SPARSE_VECTOR_NAME,
        limit=top_n,
        query_filter=build_exclusion_filter(seen),
    )


def query_hybrid(
    client: QdrantClient,
    collection: str,
    dense_vec: list[float],
    sparse_vec: models.SparseVector,
    seen: set[str],
    top_n: int = PRE_RERANK_POOL,
):
    exclusion = build_exclusion_filter(seen)
    return client.query_points(
        collection_name=collection,
        prefetch=[
            models.Prefetch(
                query=dense_vec, using=DENSE_VECTOR_NAME, limit=top_n, filter=exclusion
            ),
            models.Prefetch(
                query=sparse_vec,
                using=SPARSE_VECTOR_NAME,
                limit=top_n,
                filter=exclusion,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=top_n,
    )


# results isnt typed as pyright is having a conflict
def query_collection(
    dense_vec: list[float] | None,
    sparse_vec: models.SparseVector | None,
    client: QdrantClient,
    seen: set[str],
    collection: str = COLLECTION,
    mode: str = RETRIEVAL_MODE,
):
    try:
        if mode == "dense" and dense_vec:
            results = query_dense(client, collection, dense_vec, seen)
        elif mode == "sparse" and sparse_vec:
            results = query_sparse(client, collection, sparse_vec, seen)
        elif mode == "hybrid" and dense_vec and sparse_vec:
            results = query_hybrid(client, collection, dense_vec, sparse_vec, seen)
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
    if not USE_RERANKER:
        for c in chunks:
            logger.info("[%s] - [%s]", c.document, ", ".join(h for h in c.headers if h))
    return chunks


def _is_legislation(chunk: Payload) -> bool:
    return chunk.hierarchy in ("primary legislation", "secondary legislation")


def force_legislation_quota(
    chunks: list[Payload],
    top_n: int = FINAL_RETURN_TOP_N,
    quota_float: float = LEGISLATION_QUOTA_RATIO,
) -> list[Payload]:
    quota = round(top_n * quota_float)
    head = chunks[:top_n]
    tail = chunks[top_n:]
    legislation = [c for c in head if _is_legislation(c)]
    guidance = [c for c in head if not _is_legislation(c)]

    shortfall = quota - len(legislation)
    if shortfall > 0:
        legislation += [c for c in tail if _is_legislation(c)][:shortfall]

    final = legislation + guidance
    return final


def rerank_chunks(
    query: str,
    chunks: list[Payload],
    encoder: TextCrossEncoder,
) -> list[Payload]:
    scores = list(
        encoder.rerank(
            query,
            [f"{'\n'.join([h for h in c.headers if h])}\n\n{c.body}" for c in chunks],
        )
    )
    ranked = sorted(zip(chunks, scores), key=lambda p: p[1], reverse=True)
    payload = [
        c.model_copy(update={"rank": i + 1, "score": s})
        for i, (c, s) in enumerate(ranked)
    ]
    return payload


def normalise_ranks_and_trim(
    chunks: list[Payload], top_n: int = FINAL_RETURN_TOP_N
) -> list[Payload]:
    final = [c.model_copy(update={"rank": i + 1}) for i, c in enumerate(chunks)][:top_n]
    logger.info("chunks returned - [%s]", len(final))
    for c in final:
        logger.info("[%s] - [%s]", c.document, ", ".join(h for h in c.headers if h))
    return final


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
    for d in matched_definitions:
        logger.info("definition returned - doc: [%s], term: [%s]", d.document, d.term)
    return matched_definitions


def _dense_required(ctx: RunContext[AppDeps]) -> bool:
    return ctx.deps.mode in ("dense", "hybrid")


def _sparse_required(ctx: RunContext[AppDeps]) -> bool:
    return ctx.deps.mode in ("sparse", "hybrid")


def get_chunks_with_definitions(
    ctx: RunContext[AppDeps],
    query: str,
) -> tuple[list[Payload], list[DefinitionRecord]]:
    """Search the Isle of Man AML legislation and guidance for content relevant to the query.
    The query uses dense embedding in a Qdrant database so write the query as text as it may
    appear in the documents"""
    logger.info("qdrant queried using search phrase: [%s]", query)
    dense_vector = None
    sparse_vector = None
    if _dense_required(ctx):
        dense_vector = embed_query_dense(query, ctx.deps.dense_model)
    if _sparse_required(ctx):
        sparse_vector = embed_query_sparse(query, ctx.deps.sparse_model)
    results = query_collection(
        dense_vector,
        sparse_vector,
        ctx.deps.qdrant_client,
        mode=ctx.deps.mode,
        seen=ctx.deps.seen_chunk_ids,
    )
    chunks = return_payload(results)
    if USE_RERANKER:
        chunks = rerank_chunks(query, chunks, ctx.deps.reranker_model)
    if not ctx.deps.seen_chunk_ids:
        chunks = force_legislation_quota(chunks)
    chunks = normalise_ranks_and_trim(chunks)
    ctx.deps.seen_chunk_ids.update(c.chunk_id for c in chunks)
    definitions_data = load_definitions()
    definitions = match_definitions(chunks, definitions_data)
    return chunks, sorted(definitions, key=lambda d: (d.document, d.term))
