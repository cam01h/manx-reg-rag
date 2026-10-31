import logging

from qdrant_client import QdrantClient

from app.models import DocumentInfo
from config import COLLECTION

logger = logging.getLogger(__name__)


def load_documents(client: QdrantClient) -> list[DocumentInfo]:
    """Every document in the index, once each, with its hierarchy.

    Read from Qdrant rather than the files on disk, so the list is what the
    agent can actually search.
    """
    found: dict[str, str] = {}
    offset = None
    while True:
        points, offset = client.scroll(
            COLLECTION,
            with_payload=["document", "hierarchy"],
            with_vectors=False,
            limit=1000,
            offset=offset,
        )
        for point in points:
            payload = point.payload or {}
            found.setdefault(payload["document"], payload["hierarchy"])
        if offset is None:
            break

    # sort ignoring a leading "The" so "The AML/CFT Code" files under A
    documents = [
        DocumentInfo(name=name, hierarchy=hierarchy)
        for name, hierarchy in sorted(
            found.items(), key=lambda item: item[0].removeprefix("The ").lower()
        )
    ]
    logger.info("found %d documents in [%s]", len(documents), COLLECTION)
    return documents
