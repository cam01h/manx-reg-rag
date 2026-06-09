import json
from qdrant_client import QdrantClient, models
from config import (
    COLLECTION,
    DEFAULT_CHUNKS_RETRIEVED,
    EMBEDDING_MODEL,
    DEFINITIONS_JSONL_PATH,
    QDRANT_URL,
)
from db_ops.retrieved_chunk import RetrievedChunk, Definition
import logging

logger = logging.getLogger(__name__)


def get_chunks(
    query: str, collection: str = COLLECTION, top_n: int = DEFAULT_CHUNKS_RETRIEVED
) -> list[RetrievedChunk]:
    logger.info("qdrant queried with [%s]", query)
    try:
        client = QdrantClient(url=QDRANT_URL)
        results = client.query_points(
            collection_name=collection,
            query=models.Document(text=query, model=EMBEDDING_MODEL),
            limit=top_n,
        )
    except Exception:
        logger.exception("failed connection to qdrant")
        raise

    result_list = []
    for i, result in enumerate(results.points):
        if result.payload is None:
            raise ValueError(f"{result.id} returned no payload")
        retrieved_chunk = RetrievedChunk(
            chunk_id=result.payload["chunk_id"],
            rank=i + 1,
            score=result.score,
            document=result.payload["document"],
            hierarchy=result.payload["hierarchy"],
            major=result.payload["major"],
            minor=result.payload["minor"],
            body=result.payload["body"],
            terms_used=result.payload["terms_used"],
        )
        result_list.append(retrieved_chunk)
        logger.debug(
            "chunk retrieved - ID: %s - rank: %d - score: %.4f",
            retrieved_chunk.chunk_id,
            retrieved_chunk.rank,
            retrieved_chunk.score,
        )
    if not result_list:
        logger.info("empty result list on chunk retrieval")
    else:
        logger.info("%d results returned", len(result_list))

    return result_list


def get_definitions(chunks: list[RetrievedChunk]) -> list[Definition]:
    try:
        with open(DEFINITIONS_JSONL_PATH, "r") as f:
            definitions_by_doc = json.load(f)
    except Exception:
        logger.exception("failed connection to %s", DEFINITIONS_JSONL_PATH)
        raise
    terms_used = {}
    for chunk in chunks:
        if chunk.terms_used is None:
            logger.debug(
                "%s: terms used is None, no definitions retrieved", chunk.chunk_id
            )
            continue
        defs_found = 0
        if chunk.document in definitions_by_doc.keys():
            definitions = definitions_by_doc[chunk.document]
            for term in chunk.terms_used:
                if term in definitions.keys():
                    definition = Definition(
                        term=term, definition=definitions[term], source=chunk.document
                    )
                    terms_used[term] = definition
                    defs_found += 1
                    logger.debug("definition for [%s] found", term)
        logger.debug(
            "%s: %d definitions required - %d definitions found",
            chunk.chunk_id,
            len(chunk.terms_used),
            defs_found,
        )
    return list(terms_used.values())


def get_chunks_with_definitions(
    query: str,
) -> tuple[list[RetrievedChunk], list[Definition]]:
    """Search the Isle of Man AML legislation and guidance for content relevant to the query.
    Returns the most relevant sections from the regulations and any defined terms used in them."""
    logger.info("agent invoked get_chunks_with_definitions with query: %s", query)
    chunks = get_chunks(query)
    definitions = get_definitions(chunks)

    return chunks, definitions
