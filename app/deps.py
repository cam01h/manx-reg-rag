from dataclasses import dataclass
from qdrant_client import QdrantClient


@dataclass
class AppDeps:
    qdrant_client: QdrantClient
