import logging
import json
from pydantic_ai.models import infer_model
from qdrant_client import QdrantClient
from config import DEFINITIONS_JSONL_PATH, MODEL, QDRANT_URL

logger = logging.getLogger(__name__)


async def check_qdrant() -> None:
    try:
        client = QdrantClient(url=QDRANT_URL)
        collections = client.get_collections()
    except Exception:
        logger.exception("qdrant unreachable")
        raise
    if not collections.collections:
        logger.critical("no collections found at %s", QDRANT_URL)
        raise RuntimeError(f"no collections found at {QDRANT_URL}")
    logger.info(
        "qdrant reachable and %d collections found", len(collections.collections)
    )


async def check_definitions_file() -> None:
    try:
        raw = DEFINITIONS_JSONL_PATH.read_text()
    except Exception:
        logger.exception("unable to read file at %s", DEFINITIONS_JSONL_PATH)
        raise
    try:
        definitions = json.loads(raw)
    except json.JSONDecodeError:
        logger.exception("%s not parsable json", DEFINITIONS_JSONL_PATH)
        raise
    if not definitions:
        logger.critical("%s contains no definitions", DEFINITIONS_JSONL_PATH)
        raise RuntimeError(f"{DEFINITIONS_JSONL_PATH} contains no definitions")
    logger.info("definitions from %d documents reachable", len(definitions))


async def check_agent() -> None:
    try:
        infer_model(MODEL)
    except Exception:
        logger.exception("failed to construct MODEL: check config.py and api key")
        raise
    logger.info("%s model constructed successfully", MODEL)


async def run_startup_checks() -> None:
    logger.info("running startup checks")
    await check_qdrant()
    await check_definitions_file()
    await check_agent()
    logger.info("all startup checks passed")
