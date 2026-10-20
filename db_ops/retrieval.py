import logging
from functools import lru_cache
from pathlib import Path

import logfire
from fastembed.rerank.cross_encoder import TextCrossEncoder
from pydantic_ai import RunContext
from qdrant_client import QdrantClient, models

from app.deps import AppDeps
from config import (
    COLLECTION,
    DEFINITIONS_DIR,
    DENSE_VECTOR_NAME,
    FINAL_RETURN_TOP_N,
    LEGISLATION_QUOTA_RATIO,
    PRE_RERANK_POOL,
    RETRIEVAL_MODE,
    SPARSE_VECTOR_NAME,
    USE_RERANKER,
)

from .models import DefinitionRecord, Payload, ServedPayload
from .utils import (
    build_dense_vector,
    build_point_id,
    build_sparse_vector,
    load_jsonl_dir,
)

logger = logging.getLogger(__name__)


def build_query_filter(
    seen_ids: set[str], sectors: tuple[str, ...]
) -> models.Filter | None:
    must: list[models.Condition] = []
    must_not: list[models.Condition] = []

    if sectors:
        logger.info("filtering to sectors [%s]", ", ".join(sectors))
        must.append(
            models.FieldCondition(
                key="sectors", match=models.MatchAny(any=list(sectors))
            )
        )
    if seen_ids:
        point_ids = [build_point_id(id) for id in seen_ids]
        logger.info("excluding [%d] previously returned chunks", len(point_ids))
        must_not.append(models.HasIdCondition(has_id=point_ids))  # pyright: ignore[reportArgumentType]

    if not must and not must_not:
        return None
    return models.Filter(must=must or None, must_not=must_not or None)


def query_dense(
    client: QdrantClient,
    collection: str,
    dense_vec: list[float],
    seen: set[str],
    sectors: tuple[str, ...],
    top_n: int = PRE_RERANK_POOL,
):
    return client.query_points(
        collection_name=collection,
        query=dense_vec,
        using=DENSE_VECTOR_NAME,
        limit=top_n,
        query_filter=build_query_filter(seen, sectors),
    )


def query_sparse(
    client: QdrantClient,
    collection: str,
    sparse_vec: models.SparseVector,
    seen: set[str],
    sectors: tuple[str, ...],
    top_n: int = PRE_RERANK_POOL,
):
    return client.query_points(
        collection_name=collection,
        query=sparse_vec,
        using=SPARSE_VECTOR_NAME,
        limit=top_n,
        query_filter=build_query_filter(seen, sectors),
    )


def query_hybrid(
    client: QdrantClient,
    collection: str,
    dense_vec: list[float],
    sparse_vec: models.SparseVector,
    seen: set[str],
    sectors: tuple[str, ...],
    top_n: int = PRE_RERANK_POOL,
):
    exclusion = build_query_filter(seen, sectors)
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
    sectors: tuple[str, ...],
    collection: str = COLLECTION,
    mode: str = RETRIEVAL_MODE,
):
    try:
        if mode == "dense" and dense_vec:
            results = query_dense(client, collection, dense_vec, seen, sectors)
        elif mode == "sparse" and sparse_vec:
            results = query_sparse(client, collection, sparse_vec, seen, sectors)
        elif mode == "hybrid" and dense_vec and sparse_vec:
            results = query_hybrid(
                client, collection, dense_vec, sparse_vec, seen, sectors
            )
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
        Payload.model_validate({**r.payload, "score": r.score, "rank": i + 1})
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
def load_definitions(path: Path = DEFINITIONS_DIR) -> tuple[DefinitionRecord, ...]:
    return tuple(load_jsonl_dir(path, DefinitionRecord))


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


def repack_to_servable_chunk(chunks: list[Payload]) -> list[ServedPayload]:
    return [
        ServedPayload(
            title=f"{c.document}\n{', '.join([h for h in c.headers if h])}",
            hierarchy=c.hierarchy,
            body=c.body,
        )
        for c in chunks
    ]


def get_chunks_with_definitions(
    ctx: RunContext[AppDeps],
    query: str,
) -> tuple[list[ServedPayload], list[DefinitionRecord]]:
    """Search the Isle of Man AML legislation and guidance for content relevant to the query.
    The query uses dense embedding in a Qdrant database so do not use quotation marks,
    boolean operators, or field syntax. Write the query as a natural phrase as it would
    appear in the source text."""
    logger.info("qdrant queried using search phrase: [%s]", query)
    dense_vector = None
    sparse_vector = None
    with logfire.span("query qdrant"):
        if _dense_required(ctx):
            dense_vector = build_dense_vector(query, ctx.deps.dense_model)
        if _sparse_required(ctx):
            sparse_vector = build_sparse_vector(query, ctx.deps.sparse_model)
        results = query_collection(
            dense_vector,
            sparse_vector,
            ctx.deps.qdrant_client,
            mode=ctx.deps.mode,
            seen=ctx.deps.seen_chunk_ids,
            sectors=ctx.deps.sectors,
        )
        chunks = return_payload(results)
    if USE_RERANKER:
        with logfire.span("rerank chunks"):
            chunks = rerank_chunks(query, chunks, ctx.deps.reranker_model)
    if not ctx.deps.seen_chunk_ids:
        chunks = force_legislation_quota(chunks)
    chunks = normalise_ranks_and_trim(chunks)
    ctx.deps.seen_chunk_ids.update(c.chunk_id for c in chunks)
    with logfire.span("attach denfinitions"):
        definitions_data = load_definitions()
        definitions = match_definitions(chunks, definitions_data)
    chunks = repack_to_servable_chunk(chunks)
    return chunks, sorted(definitions, key=lambda d: (d.document, d.term))
