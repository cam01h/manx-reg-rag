from dataclasses import dataclass
from fastembed import TextEmbedding
from qdrant_client import QdrantClient


@dataclass
class AppDeps:
    qdrant_client: QdrantClient
    embedding_model: TextEmbedding
