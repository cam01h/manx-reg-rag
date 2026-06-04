from pathlib import Path

# ==========
# file paths
# ==========
project_root = Path(__file__).parent
# Intermediate
CHUNKS_JSONL_PATH = project_root / "data/processed/chunks.jsonl"
DEFINITIONS_JSONL_PATH = project_root / "data/processed/definitions.json"
# db path
DB_PATH = project_root / "data/qdrant"
# Testing
MD_1 = project_root / "tests/md_test_1.md"
MD_2 = project_root / "tests/md_test_2.md"
MD_3 = project_root / "tests/md_test_3.md"

# =========
# Chunks
# =========
MAX_CHUNK_CHAR = 1500
TARGET_CHUNK_CHAR = 1000
MIN_CHUNK_CHAR = 500
DELETE_LEN = 40

# =========
# Models
# =========
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
COLLECTION = "manx-reg-rag-db"


def get_embedding_dim(embedding_model):
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=embedding_model).embedding_size
