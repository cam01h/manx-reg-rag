from qdrant_client import QdrantClient, models
from config import DB_PATH, EMBEDDING_MODEL, COLLECTION

client = QdrantClient(path=str(DB_PATH))
QUERY = "What do i need to do with a customer thats a politically exposed person?"


def retrieve(query: str, collection: str = COLLECTION, top_n: int = 5):
    results = client.query_points(
        collection_name=collection,
        query=models.Document(text=query, model=EMBEDDING_MODEL),
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
    print("==========")
    print(f"Query: {QUERY}")
    for result in results:
        print(f"Rank: {result['rank']}")
        print(f"Score: {result['score']}")
        print(f"Document: {result['payload']['document']}")
        print(f"Major Heading: {result['payload']['major']}")
        print(f"Minor Heading: {result['payload']['minor']}")
        print(f"{result['payload']['body']}")
        print("----------")
