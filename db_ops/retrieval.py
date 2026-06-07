import json
from qdrant_client import QdrantClient, models
from config import (
    COLLECTION,
    DEFAULT_CHUNKS_RETREIVED,
    EMBEDDING_MODEL,
    DEFINITIONS_JSONL_PATH,
    QDRANT_URL,
)
from db_ops.retrieved_chunk import RetrievedChunk, Definition


def get_chunks(
    query: str, collection: str = COLLECTION, top_n: int = DEFAULT_CHUNKS_RETREIVED
) -> list[RetrievedChunk]:
    client = QdrantClient(url=QDRANT_URL)
    results = client.query_points(
        collection_name=collection,
        query=models.Document(text=query, model=EMBEDDING_MODEL),
        limit=top_n,
    )

    result_list = []
    for i, result in enumerate(results.points):
        if result.payload is None:
            raise ValueError(f"{result.id} returned no payload")
        retrieved_chunk = RetrievedChunk(
            chunk_id=result.payload["chunk_id"],
            rank=i + 1,
            score=result.score,
            document=result.payload["document"],
            hierarchy=result.payload["hierarchy"],
            major=result.payload["major"],
            minor=result.payload["minor"],
            body=result.payload["body"],
            terms_used=result.payload["terms_used"],
        )
        result_list.append(retrieved_chunk)

    return result_list


def get_definitions(chunks: list[RetrievedChunk]) -> list[Definition]:
    with open(DEFINITIONS_JSONL_PATH, "r") as f:
        defintions_by_doc = json.load(f)
    terms_used = {}
    for chunk in chunks:
        if chunk.terms_used is None:
            continue
        if chunk.document in defintions_by_doc.keys():
            definitions = defintions_by_doc[chunk.document]
            for term in chunk.terms_used:
                if term in definitions.keys():
                    defintion = Definition(
                        term=term, defintion=definitions[term], source=chunk.document
                    )
                    terms_used[term] = defintion
    return list(terms_used.values())


def get_chunks_with_definitions(
    query: str,
) -> tuple[list[RetrievedChunk], list[Definition]]:
    """Search the Isle of Man AML legislation and guidance for content relevant to the query.
    Returns the most relevant sections from the regulations and any defined terms used in them."""
    chunks = get_chunks(query)
    definitions = get_definitions(chunks)
    print(f"query ran for {query}")
    for chunk in chunks:
        print({chunk.major} - {chunk.minor})

    return chunks, definitions
