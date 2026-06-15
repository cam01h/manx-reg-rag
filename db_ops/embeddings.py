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
import hashlib
import logging

logger = logging.getLogger(__name__)


def get_body_hash(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:8]


def build_collection(input_path: Path, collection: str) -> None:
    logger.info(
        "build collection called on %s to create collection: %s", input_path, collection
    )
    client = QdrantClient(url=QDRANT_URL)

    try:
        if client.collection_exists(collection):
            client.delete_collection(collection)
            logger.info("existing %s collection deleted", collection)
        client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(
                size=get_embedding_dim(EMBEDDING_MODEL), distance=models.Distance.COSINE
            ),
        )
        logger.info("collection %s created", collection)
    except Exception:
        logger.exception("failed to create collection")
        raise

    try:
        chunks = [json.loads(line) for line in input_path.read_text().splitlines()]
        logger.info("loaded %s into %d chunks", input_path, len(chunks))
    except Exception:
        logger.exception("failed to read to %s", input_path)
        raise

    points = []
    for c in chunks:
        chunk_id = (
            f"{c['document']}::{'::'.join(c['headers'])}::{get_body_hash(c['body'])}"
        )
        try:
            point = models.PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id)),
                vector=models.Document(
                    text=f"{'\n'.join(c['headers'])}\n{c['body']}",
                    model=EMBEDDING_MODEL,
                ),
                payload={**c, "chunk_id": chunk_id},
            )
        except Exception:
            logger.exception("failed to create point for %s", chunk_id)
            raise
        points.append(point)
    logger.info(
        "%d points created from %d chunks",
        len(points),
        len(chunks),
    )

    try:
        client.upsert(collection_name=collection, points=points)
        logger.info(
            "upsert complete, %d points embedded",
            client.count(collection_name=collection).count,
        )
    except Exception:
        logger.exception("failed to upsert collection")
        raise


if __name__ == "__main__":
    setup_logging("embedding")
    build_collection(CHUNKS_JSONL_PATH, COLLECTION)
