import argparse
import logging
from dataclasses import asdict
from pathlib import Path

from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient, models

from config import (
    CHUNKS_DIR,
    COLLECTION,
    DENSE_MODEL_NAME,
    QDRANT_URL,
    SPARSE_MODEL_NAME,
    setup_logging,
)
from extraction_ops.models import Chunk

from .utils import (
    build_dense_vector,
    build_point_id,
    build_sparse_vector,
    load_jsonl_dir,
)

logger = logging.getLogger(__name__)

DENSE_MODEL = TextEmbedding(DENSE_MODEL_NAME)
SPARSE_MODEL = SparseTextEmbedding(SPARSE_MODEL_NAME)


def get_existing_point_ids(client: QdrantClient) -> set[str]:
    point_ids: set[str] = set()
    offset_id = None
    while True:
        points = client.scroll(
            collection_name=COLLECTION,
            offset=offset_id,
            limit=1000,
            with_payload=False,
            with_vectors=False,
        )
        point_ids.update(str(record.id) for record in points[0])
        offset_id = points[1]
        if offset_id is None:
            break
    return point_ids


def build_embedding_text(chunk: Chunk) -> str:
    return f"{'\n'.join(h for h in chunk.headers if h)}\n{chunk.body}"


def build_point(
    chunk: Chunk,
    dense_vec: list[float],
    sparse_vec: models.SparseVector,
) -> models.PointStruct:
    try:
        point = models.PointStruct(
            id=build_point_id(chunk.chunk_id),
            vector={"dense": dense_vec, "bm25": sparse_vec},
            payload=asdict(chunk),
        )
    except Exception:
        logger.exception("failed to create point for [%s]", chunk.chunk_id)
        raise
    return point


def build_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tool for embedding chunks as vectors and payloads in Qdrant"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete all db entries and recreate. Should be used when changing embedding model",
    )
    return parser.parse_args()


def create_collection(
    client: QdrantClient, collection: str, rebuild: bool = False
) -> None:
    try:
        exists = client.collection_exists(collection)
        if exists and rebuild:
            client.delete_collection(collection)
            logger.info("existing [%s] collection deleted", collection)
            exists = False
        if exists:
            logger.info("using existing [%s] collection", collection)
            return
        client.create_collection(
            collection_name=collection,
            vectors_config={
                "dense": models.VectorParams(
                    size=DENSE_MODEL.embedding_size,
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
    key = "sectors"
    try:
        client.create_payload_index(
            collection_name=collection,
            field_name=key,
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        logger.info("indexed [%s] field", key)
    except Exception:
        logger.exception("failed to index [%s] field", key)
        raise


def embed_chunk(chunk: Chunk) -> models.PointStruct:
    text = build_embedding_text(chunk)
    return build_point(
        chunk,
        build_dense_vector(text, DENSE_MODEL),
        build_sparse_vector(text, SPARSE_MODEL),
    )


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


def delete_stale_points(
    client: QdrantClient, chunks: list[Chunk], existing_ids: set[str]
) -> None:
    ids_from_jsonl = {build_point_id(c.chunk_id) for c in chunks}
    points_to_delete = [id for id in existing_ids if id not in ids_from_jsonl]
    if not points_to_delete:
        logger.info("no stale points to delete")
        return
    try:
        client.delete(
            collection_name=COLLECTION,
            points_selector=models.PointIdsList(points=list(points_to_delete)),
        )
    except Exception:
        logger.exception("failed to delete stale points")
        raise
    logger.info("successfully deleted [%d] stale points", len(points_to_delete))


def update_payloads(
    client: QdrantClient, chunks: list[Chunk], existing_ids: set[str]
) -> None:
    kept = [c for c in chunks if build_point_id(c.chunk_id) in existing_ids]
    if not kept:
        logger.info("no existing points to refresh")
        return
    try:
        client.batch_update_points(
            collection_name=COLLECTION,
            update_operations=[
                models.OverwritePayloadOperation(
                    overwrite_payload=models.SetPayload(
                        payload=asdict(c),
                        points=[build_point_id(c.chunk_id)],
                    )
                )
                for c in kept
            ],
        )
    except Exception:
        logger.exception("failed to refresh payloads")
        raise
    logger.info("refreshed payloads on [%d] existing points", len(kept))


def build_collection(chunk_dir: Path, collection: str, rebuild: bool = False) -> None:
    chunks: list[Chunk] = load_jsonl_dir(chunk_dir, Chunk)
    client = QdrantClient(url=QDRANT_URL)
    create_collection(client, collection, rebuild)
    existing_ids = get_existing_point_ids(client)
    new_chunks = [c for c in chunks if build_point_id(c.chunk_id) not in existing_ids]
    logger.info("embedding [%d] new chunks", len(new_chunks))
    points = [embed_chunk(c) for c in new_chunks]
    upload_collection(client, collection, points)
    delete_stale_points(client, chunks, existing_ids)
    update_payloads(client, chunks, existing_ids)


if __name__ == "__main__":
    setup_logging("embedding")
    args = build_cli()
    build_collection(CHUNKS_DIR, COLLECTION, args.rebuild)
