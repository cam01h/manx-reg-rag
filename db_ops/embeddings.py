import json
import uuid
from qdrant_client import QdrantClient, models
from config import CHUNKS_JSONL_PATH, DB_PATH, EMBEDDING_MODEL, get_embedding_dim
import hashlib


def build_collection(input_path, db_path, collection):
    client = QdrantClient(path=str(db_path))

    if client.collection_exists(collection):
        client.delete_collection(collection)

    client.create_collection(
        collection_name=collection,
        vectors_config=models.VectorParams(
            size=get_embedding_dim(EMBEDDING_MODEL), distance=models.Distance.COSINE
        ),
    )

    def get_body_hash(text: str) -> str:
        return hashlib.sha1(text.encode()).hexdigest()[:8]

    chunks = [json.loads(line) for line in input_path.read_text().splitlines()]
    points = []
    for c in chunks:
        chunk_id = (
            f"{c['document']}::{c['major']}::{c['minor']}::{get_body_hash(c['body'])}"
        )
        point = models.PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id)),
            vector=models.Document(
                text=f"{c['major']}\n{c['minor']}\n{c['body']}", model=EMBEDDING_MODEL
            ),
            payload={**c, "chunk_id": chunk_id},
        )
        points.append(point)

    client.upsert(collection_name=collection, points=points)

    print(client.count(collection_name=collection))


if __name__ == "__main__":
    build_collection(CHUNKS_JSONL_PATH, DB_PATH, "manx-reg-rag-db")
