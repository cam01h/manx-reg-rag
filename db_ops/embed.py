from dataclasses import asdict
import json
import uuid
from pathlib import Path
from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient, models
from config import (
    CHUNKS_JSONL_PATH,
    COLLECTION,
    DENSE_MODEL_NAME,
    QDRANT_URL,
    SPARSE_MODEL_NAME,
    get_embedding_dim,
    setup_logging,
)
import logging
from extraction_ops.models import Chunk

logger = logging.getLogger(__name__)

DENSE_MODEL = TextEmbedding(DENSE_MODEL_NAME)
SPARSE_MODEL = SparseTextEmbedding(SPARSE_MODEL_NAME)


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


def build_embedding_text(chunk: Chunk) -> str:
    return f"{'\n'.join(h for h in chunk.headers if h)}\n{chunk.body}"


def build_dense_vector(chunk: Chunk, model: TextEmbedding) -> list[float]:
    return list(model.embed([build_embedding_text(chunk)]))[0].tolist()


def build_sparse_vector(
    chunk: Chunk, model: SparseTextEmbedding
) -> models.SparseVector:
    emb = list(model.embed([build_embedding_text(chunk)]))[0]
    vector = models.SparseVector(
        indices=emb.indices.tolist(),
        values=emb.values.tolist(),
    )
    return vector


def build_point(
    chunk: Chunk,
    dense_vec: list[float],
    sparse_vec: models.SparseVector,
) -> models.PointStruct:
    try:
        point = models.PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.chunk_id)),
            vector={"dense": dense_vec, "bm25": sparse_vec},
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
            vectors_config={
                "dense": models.VectorParams(
                    size=get_embedding_dim(DENSE_MODEL_NAME),
                    distance=models.Distance.COSINE,
                )
            },
            sparse_vectors_config={
                "bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)
            },
        )
        logger.info("collection [%s] created", collection)
    except Exception:
        logger.exception("failed to create collection")
        raise


def upload_collection(
    client: QdrantClient, collection: str, points: list[models.PointStruct]
) -> None:
    try:
        client.upload_points(collection_name=collection, points=points, batch_size=64)
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
    vectors = [
        (
            c,
            build_dense_vector(c, DENSE_MODEL),
            build_sparse_vector(c, SPARSE_MODEL),
        )
        for c in chunks
    ]
    points = [build_point(v[0], v[1], v[2]) for v in vectors]
    upload_collection(client, collection, points)


if __name__ == "__main__":
    setup_logging("embedding")
    build_collection(CHUNKS_JSONL_PATH, COLLECTION)
