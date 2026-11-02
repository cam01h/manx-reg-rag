from dataclasses import dataclass, field

from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient

from db_ops.models import Payload


@dataclass
class AppDeps:
    qdrant_client: QdrantClient
    dense_model: TextEmbedding
    sparse_model: SparseTextEmbedding
    reranker_model: TextCrossEncoder
    mode: str
    served: dict[str, Payload] = field(default_factory=dict)
    sectors: tuple[str, ...] = ()

    def seen_ids(self) -> set[str]:
        return {p.chunk_id for p in self.served.values()}

    def next_ref(self) -> str:
        return f"C{len(self.served) + 1:03d}"
