"""Fakes for testing db_ops.verify without a Qdrant server or real embedding models."""

import zlib
from dataclasses import asdict
from types import SimpleNamespace

import numpy as np
from qdrant_client import QdrantClient, models

from config import DENSE_VECTOR_NAME, SPARSE_VECTOR_NAME
from core.sectors import SECTORS_FIELD
from db_ops.utils import (
    build_dense_vector,
    build_embedding_text,
    build_point_id,
    build_sparse_vector,
)
from extraction_ops.models import Chunk

DIM = 8


class FakeDense:
    """Gives the same vector for the same text and salt, a different one for a new salt."""

    def __init__(self, salt: str = "a"):
        self.salt = salt

    def embed(self, texts):
        for text in texts:
            rng = np.random.default_rng(zlib.crc32(f"{self.salt}{text}".encode()))
            yield rng.normal(size=DIM).astype(np.float32)


class FakeSparse:
    def __init__(self, salt: str = "a"):
        self.salt = salt

    def embed(self, texts):
        for text in texts:
            indices = sorted(
                {zlib.crc32(f"{self.salt}{w}".encode()) % 1000 for w in text.split()}
            )
            yield SimpleNamespace(
                indices=np.array(indices, dtype=np.int64),
                values=np.array([1.0 + i % 3 for i in range(len(indices))], np.float32),
            )


def make_chunk(i: int, document: str = "Doc A", **overrides) -> Chunk:
    fields = {
        "chunk_id": f"{document}, Part {i} - hash{i:04d}",
        "document": document,
        "hierarchy": "primary legislation",
        "sectors": ("class_1", "class_2"),
        "headers": [f"Part {i}"],
        "body": f"body of part {i} with some words in it",
        "url": "https://example.com/doc.pdf",
        "terms_used": None,
    }
    fields.update(overrides)
    return Chunk(**fields)


def make_chunks() -> list[Chunk]:
    return [make_chunk(i, "Doc A") for i in range(4)] + [
        make_chunk(i, "Doc B") for i in range(10, 13)
    ]


def make_point(
    chunk: Chunk, dense: FakeDense, sparse: FakeSparse
) -> models.PointStruct:
    text = build_embedding_text(chunk)
    return models.PointStruct(
        id=build_point_id(chunk.chunk_id),
        vector={
            DENSE_VECTOR_NAME: build_dense_vector(text, dense),
            SPARSE_VECTOR_NAME: build_sparse_vector(text, sparse),
        },
        payload=asdict(chunk),
    )


def populate(
    client: QdrantClient,
    collection: str,
    chunks: list[Chunk],
    dense: FakeDense | None = None,
    sparse: FakeSparse | None = None,
) -> None:
    """Build a collection shaped like the one db_ops/embed.py creates, and fill it."""
    dense, sparse = dense or FakeDense(), sparse or FakeSparse()
    client.create_collection(
        collection_name=collection,
        vectors_config={
            DENSE_VECTOR_NAME: models.VectorParams(
                size=DIM, distance=models.Distance.COSINE
            )
        },
        sparse_vectors_config={
            SPARSE_VECTOR_NAME: models.SparseVectorParams(modifier=models.Modifier.IDF)
        },
    )
    client.upsert(collection, [make_point(c, dense, sparse) for c in chunks])


def fake_client(
    size: int = DIM,
    distance: models.Distance = models.Distance.COSINE,
    dense_name: str = DENSE_VECTOR_NAME,
    sparse_name: str | None = SPARSE_VECTOR_NAME,
    modifier: models.Modifier = models.Modifier.IDF,
    index: models.PayloadSchemaType | None = models.PayloadSchemaType.KEYWORD,
):
    """Just enough of a client for check_config. The in-memory client has no payload indexes."""
    sparse_vectors = (
        {sparse_name: models.SparseVectorParams(modifier=modifier)}
        if sparse_name
        else None
    )
    info = SimpleNamespace(
        config=SimpleNamespace(
            params=SimpleNamespace(
                vectors={dense_name: models.VectorParams(size=size, distance=distance)},
                sparse_vectors=sparse_vectors,
            )
        ),
        payload_schema={SECTORS_FIELD: SimpleNamespace(data_type=index)}
        if index
        else {},
    )
    return SimpleNamespace(get_collection=lambda name: info)
