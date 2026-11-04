import logging
from pathlib import Path

from pydantic_ai.models import infer_model
from qdrant_client import QdrantClient

from config import (
    CHUNKS_DIR,
    COLLECTION,
    DEFINITIONS_DIR,
    MODEL,
    QDRANT_URL,
)
from db_ops.utils import load_jsonl_dir
from db_ops.verify import check_config, check_counts, check_indexes
from extraction_ops.models import Chunk, Definition

logger = logging.getLogger(__name__)


async def check_qdrant() -> None:
    try:
        client = QdrantClient(url=QDRANT_URL)
        collections = client.get_collections()
        collection_info = client.get_collection(COLLECTION)
    except Exception:
        logger.exception("qdrant unreachable")
        raise
    if not collections.collections:
        logger.critical("no collections found at %s", QDRANT_URL)
        raise RuntimeError(f"no collections found at {QDRANT_URL}")
    logger.info(
        "qdrant reachable and %d collections found", len(collections.collections)
    )
    if not collection_info.points_count:
        logger.critical("collection [%s] has no points", COLLECTION)
        raise RuntimeError(f"collection [{COLLECTION}] has no points")
    logger.info(
        "collection [%s] has [%d] points",
        COLLECTION,
        collection_info.points_count,
    )


async def check_definitions_file() -> None:
    definitions = load_jsonl_dir(DEFINITIONS_DIR, Definition)
    if not definitions:
        logger.critical("[%s] contains no definitions", DEFINITIONS_DIR)
        raise RuntimeError(f"[{DEFINITIONS_DIR}] contains no definitions")
    logger.info("definitions from %d documents reachable", len(definitions))


async def check_index_matches_data(
    dense_size: int,
    client: QdrantClient | None = None,
    chunk_dir: Path = CHUNKS_DIR,
) -> None:
    """Refuse to start when the collection and the chunk jsonl have drifted apart.

    The usual cause is a deploy that pulled new jsonl without running `mrr embed`.
    """
    client = client or QdrantClient(url=QDRANT_URL)
    chunks = load_jsonl_dir(chunk_dir, Chunk)
    problems = check_counts(client, COLLECTION, chunks) + check_config(
        client, COLLECTION, dense_size
    )
    if problems:
        for problem in problems:
            logger.critical("%s", problem)
        logger.critical("qdrant does not match the chunk jsonl: run mrr embed")
        raise RuntimeError(
            f"collection [{COLLECTION}] does not match the chunk jsonl: run mrr embed"
        )
    # a missing index only slows sector-filtered searches, so it warns instead of stopping the app
    for problem in check_indexes(client, COLLECTION):
        logger.warning("%s (searches still work, they are just slower)", problem)
    logger.info(
        "collection [%s] matches the [%d] chunks in the jsonl", COLLECTION, len(chunks)
    )


async def check_agent() -> None:
    try:
        infer_model(MODEL)
    except Exception:
        logger.exception("failed to construct MODEL: check config.py and api key")
        raise
    logger.info("%s model constructed successfully", MODEL)


async def run_startup_checks(dense_size: int) -> None:
    logger.info("running startup checks")
    await check_qdrant()
    await check_index_matches_data(dense_size)
    await check_definitions_file()
    await check_agent()
    logger.info("all startup checks passed")
