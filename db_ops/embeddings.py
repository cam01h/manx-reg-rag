import json
from qdrant_client import QdrantClient, models
from config import CHUNKS_JSONL_PATH, DB_PATH, EMBEDDING_MODEL, get_embedding_dim


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

    chunks = [json.loads(line) for line in input_path.read_text().splitlines()]
    points = []
    for i, c in enumerate(chunks):
        point = models.PointStruct(
            id=i + 1,
            vector=models.Document(
                text=f"{c['major']}\n{c['minor']}\n{c['body']}", model=EMBEDDING_MODEL
            ),
            payload=c,
        )
        points.append(point)

    client.upsert(collection_name=collection, points=points)

    # client.add(collection_name=collection, documents=documents, metadata=chunks)
    print(client.count(collection_name=collection))


if __name__ == "__main__":
    build_collection(CHUNKS_JSONL_PATH, DB_PATH, "manx-reg-rag-db")
