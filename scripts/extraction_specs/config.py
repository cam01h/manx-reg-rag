from pathlib import Path

# ==========
# file paths
# ==========
project_root = Path(__file__).parent.parent.parent
# inputs
AML_CODE_RAW_PATH = project_root / "data/raw/custom/the_aml_code_2019.pdf"
AML_HANDBOOK_PATH = project_root / "data/raw/custom/aml_handbook_april_2026.pdf"
# Intermediate
AML_CODE_JSONL_PATH = project_root / "data/processed/raw_code.jsonl"
AML_CODE_MD_PATH = project_root / "data/processed/raw_code.md"
AML_CODE_DEF_PATH = project_root / "data/processed/code_defs.json"
# db path
DB_PATH = project_root / "data/qdrant"

# =========
# Chunks
# =========
MAX_CHUNK_CHAR = 1500

# =========
# Models
# =========
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


def get_embedding_dim(embedding_model):
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=embedding_model).embedding_size
