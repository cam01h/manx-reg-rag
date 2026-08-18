from dataclasses import asdict
import json
import uuid
from pathlib import Path
from qdrant_client import QdrantClient, models
from config import (
    CHUNKS_JSONL_PATH,
    COLLECTION,
    EMBEDDING_MODEL,
    QDRANT_URL,
    get_embedding_dim,
    setup_logging,
)
import logging
from extraction_ops.models import Chunk

logger = logging.getLogger(__name__)


def load_chunks(path: Path) -> list[Chunk]:
    if not path.exists():
        logger.critical("no chunks jsonl file found at [%s]", path)
        raise FileNotFoundError
    try:
        chunks = [Chunk(**json.loads(line)) for line in path.read_text().splitlines()]
        logger.info("loaded [%s] into [%d] chunks", path, len(chunks))
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        logger.exception("failed to read to [%s]", path)
        raise
    return chunks


def build_point(chunk: Chunk) -> models.PointStruct:
    try:
        point = models.PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.chunk_id)),
            vector=models.Document(
                text=f"{'\n'.join(h for h in chunk.headers if h)}\n{chunk.body}",
                model=EMBEDDING_MODEL,
            ),
            payload=asdict(chunk),
        )
    except Exception:
        logger.exception("failed to create point for [%s]", chunk.chunk_id)
        raise
    return point


def create_collection(client: QdrantClient, collection: str) -> None:
    try:
        if client.collection_exists(collection):
            client.delete_collection(collection)
            logger.info("existing [%s] collection deleted", collection)
        client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(
                size=get_embedding_dim(EMBEDDING_MODEL), distance=models.Distance.COSINE
            ),
        )
        logger.info("collection [%s] created", collection)
    except Exception:
        logger.exception("failed to create collection")
        raise


def upsert_collection(
    client: QdrantClient, collection: str, points: list[models.PointStruct]
) -> None:
    try:
        client.upsert(collection_name=collection, points=points)
        logger.info(
            "upsert complete, [%d] points embedded",
            client.count(collection_name=collection).count,
        )
    except Exception:
        logger.exception("failed to upsert collection")
        raise


def build_collection(input_path: Path, collection: str) -> None:
    chunks = load_chunks(input_path)
    client = QdrantClient(url=QDRANT_URL)
    create_collection(client, collection)
    points = [build_point(c) for c in chunks]
    upsert_collection(client, collection, points)


if __name__ == "__main__":
    setup_logging("embedding")
    build_collection(CHUNKS_JSONL_PATH, COLLECTION)
