from qdrant_client import QdrantClient, models
from pathlib import Path
from globals import DB_PATH, EMBEDDING_MODEL

project_root = Path(__file__).parent.parent
client = QdrantClient(path=str(DB_PATH))
QUERY = "under what circumstances is enhanced customer duediligence require?"


def retrieve(query: str, collection: str = "aml_code_test", top_n: int = 5):
    results = client.query_points(
        collection_name=collection,
        query=models.Document(text=query, model=EMBEDDING_MODEL),
        using="fast-bge-small-en",
        limit=top_n,
    )

    result_list = []
    for i, result in enumerate(results.points):
        details = {}
        details["payload"] = result.payload
        details["score"] = result.score
        details["rank"] = i + 1
        result_list.append(details)

    return result_list


if __name__ == "__main__":
    results = retrieve(QUERY)
    for result in results:
        print(f"Rank: {result['rank']}")
        print(f"Score: {result['score']}")
        print(f"Payload: {result['payload']['paragraph']}")
