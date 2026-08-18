import json
from pathlib import Path
from qdrant_client import QdrantClient, models
from config import (
    COLLECTION,
    DEFAULT_CHUNKS_RETRIEVED,
    EMBEDDING_MODEL,
    DEFINITIONS_JSONL_PATH,
)
from db_ops.models import DefinitionRecord, Payload
from pydantic_ai import RunContext
from app.deps import AppDeps
import logging

logger = logging.getLogger(__name__)


# results isnt typed as pyright is having a conflict with two types of th same name
def query_collection(
    query: str,
    client: QdrantClient,
    collection: str = COLLECTION,
    top_n: int = DEFAULT_CHUNKS_RETRIEVED,
):
    logger.info("qdrant queried using search phrase: [%s]", query)
    logger.info("qdrant queried with [%s]", query)
    try:
        results = client.query_points(
            collection_name=collection,
            query=models.Document(text=query, model=EMBEDDING_MODEL),
            limit=top_n,
        )
    except Exception:
        logger.exception("failed connection to qdrant")
        raise
    if not results:
        logger.critical("no results found from query")
        raise ValueError("no results found from query")
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


def load_definitions(path: Path = DEFINITIONS_JSONL_PATH) -> list[DefinitionRecord]:
    if not path.exists():
        logger.critical("no definitions jsonl file found at [%s]", path)
        raise FileNotFoundError(f"no definitions jsonl file found at [{path}]")
    try:
        definitions = [
            DefinitionRecord(**json.loads(line))
            for line in path.read_text().splitlines()
        ]
    except (json.JSONDecodeError, TypeError):
        logger.exception("failed to read to [%s]", path)
        raise
    return definitions


def match_definitions(
    chunks: list[Payload], definitions: list[DefinitionRecord]
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
) -> tuple[list[Payload], set[DefinitionRecord]]:
    """Search the Isle of Man AML legislation and guidance for content relevant to the query.
    Returns the most relevant sections from the regulations and any defined terms used in them."""
    results = query_collection(query, ctx.deps.qdrant_client)
    chunks = return_payload(results)
    definitions_data = load_definitions()
    definitions = match_definitions(chunks, definitions_data)
    return chunks, definitions
