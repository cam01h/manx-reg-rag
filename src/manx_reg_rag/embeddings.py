import json
from qdrant_client import QdrantClient
from globals import AML_CODE_JSONL_PATH, DB_PATH


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
    build_collection(AML_CODE_JSONL_PATH, DB_PATH, "aml_code_test")
