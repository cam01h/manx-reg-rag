import datetime as dt
import logging
import logging.config
import os
from pathlib import Path

# ==========
# file paths
# ==========
PROJECT_ROOT = Path(__file__).parent
# Intermediate
CHUNKS_DIR = PROJECT_ROOT / "data/processed/chunks/"
DEFINITIONS_DIR = PROJECT_ROOT / "data/processed/definitions/"
# db path
DB_PATH = PROJECT_ROOT / "data/qdrant"
# Testing
EXTRACTION_OPS_TEST_DATA = PROJECT_ROOT / "tests/extraction_ops/diagnostics/data"
# Agent
SYSTEM_PROMPT_PATH = PROJECT_ROOT / "system_prompt.md"

# =========
# Chunks
# =========
MAX_CHUNK_CHAR = 1500
TARGET_CHUNK_CHAR = 1000
MIN_CHUNK_CHAR = 500
DELETE_LEN = 40

# =========
# Containerisation
# =========
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

# =========
# DB ops
# =========
RETRIEVAL_MODE = "hybrid"  # "dense" | "sparse" | "hybrid"
DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "bm25"
DENSE_MODEL_NAME = "BAAI/bge-large-en-v1.5"  # "BAAI/bge-small-en-v1.5"
SPARSE_MODEL_NAME = "Qdrant/bm25"
RERANKING_MODEL_NAME = "jinaai/jina-reranker-v1-turbo-en"
USE_RERANKER = True
COLLECTION = "manx-reg-rag-db"
PRE_RERANK_POOL = 50
FINAL_RETURN_TOP_N = 10
LEGISLATION_QUOTA_RATIO = 0.5
PAYLOAD_UPDATE_BATCH_SIZE = 100

# ========
# Agent
# ========
MODEL = "openai-responses:gpt-5.6-luna"
REASONING_EFFORT = "medium"

SYSTEM_PROMPT = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


# logging and logfire
SERVICE_NAME = "manx-reg-rag"
SEND_TO_LOGFIRE = os.getenv("SEND_TO_LOGFIRE", "false").lower() == "true"


def setup_logging(entry_point: str) -> None:
    date = dt.datetime.today()
    logfile = (
        PROJECT_ROOT
        / f"logs/{entry_point}-{date.year}-{date.month:02d}-{date.day:02d}.log"
    )
    logfile.parent.mkdir(exist_ok=True)
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": "%(asctime)s::%(name)s::%(levelname)s::%(message)s"}
        },
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "formatter": "default",
                "filename": str(logfile),
                "encoding": "utf-8",
                "level": "DEBUG",
            },
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": "INFO",
            },
        },
        "loggers": {
            # mute all but warnings from built in loggers
            "uvicorn": {"level": "WARNING"},
            "uvicorn.access": {"level": "WARNING"},
            "uvicorn.error": {"level": "INFO"},
            "httpx": {"level": "WARNING"},
            "httpcore": {"level": "WARNING"},
            "qdrant_client": {"level": "WARNING"},
            "fastembed": {"level": "WARNING"},
            "openai": {"level": "WARNING"},
            "hugging_face_hub": {"level": "WARNING"},
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["file", "console"],
        },
    }
    logging.config.dictConfig(config)
