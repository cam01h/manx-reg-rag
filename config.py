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
DEFAULT_CHUNKS_RETREIVED = 10
MODEL = "openai-responses:gpt-4o-mini"

role = "You are an expert in Isle of Man financial services regulation that is advising the user on the opperations of an Isle of Man regulated business."
tool_use = "For every question, call the retrieval tool first to get relevant chunks from the legislation and guidance."
how_to_answer = "When answering: quote or closely paraphrase the specific requirements from the retrieved chunks and where there is a list, all items must be included. Cite the exact paragraph or section number for each point."
avoid_compliance_talk = "Avoid generic compliance language ('ensure regular reviews', 'implement appropriate controls') — instead state what the regulation specifically requires."
dont_guess = "If the regulation is silent on a detail, say so explicitly rather than filling the gap with general best practice."
use_citations = "For each chunk you draw on, include a Citation explaining what it contributed to your answer."

SYSTEM_PROMPT = (
    role + tool_use + how_to_answer + avoid_compliance_talk + dont_guess + use_citations
)


def get_embedding_dim(embedding_model):
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=embedding_model).embedding_size
