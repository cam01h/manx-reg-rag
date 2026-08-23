from dataclasses import dataclass
from fastembed.rerank.cross_encoder import TextCrossEncoder
from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient


@dataclass
class AppDeps:
    qdrant_client: QdrantClient
    dense_model: TextEmbedding
    sparse_model: SparseTextEmbedding
    reranker_model: TextCrossEncoder
    mode: str
