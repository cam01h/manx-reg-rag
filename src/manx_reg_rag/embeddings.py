import json
from pathlib import Path
from qdrant_client import QdrantClient


def build_collection(input_path, db_path, collection):
    client = QdrantClient(path=str(db_path))

    # TODO: locate all jsonl files in the processed directory
    chunks = [json.loads(line) for line in input_path.read_text().splitlines()]

    documents = [chunk["body"] for chunk in chunks]

    if client.collection_exists(collection):
        client.delete_collection(collection)
    client.add(collection_name=collection, documents=documents, metadata=chunks)
    print(client.count(collection_name=collection))


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    chunks_path = project_root / "data/processed/raw_code.jsonl"
    db_path = project_root / "data/qdrant"
    build_collection(chunks_path, db_path, "aml_code_test")
