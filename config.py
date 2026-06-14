import logging
import logging.config
import datetime as dt
from pathlib import Path
import os

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
CLEAN_MD = project_root / "tests/clean.md"
TRIMMED_MD = project_root / "tests/trimmed.md"
CHUNKS_MD = project_root / "tests/chunks.md"
DEFINITIONS_MD = project_root / "tests/definitions.md"

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
# Models
# =========
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
COLLECTION = "manx-reg-rag-db"
DEFAULT_CHUNKS_RETRIEVED = 10
MODEL = "openai-responses:gpt-4o-mini"

SYSTEM_PROMPT = """You are an expert in Isle of Man financial services regulation.
        The user is a member of a regulated Isle of Man financial services firm.

        You must use the tools to call information from the regulatory corpus. You 
        should use the tools as many times as is nessisary in as many ways as you see 
        fit until you are satistfied you have all the information nessisary to answer.
        You must only ever answer using the information received for tool calls and 
        never using information from any other sources. 

        The answer must directly answer directly. Never shorten or merge concepts from 
        the source documents and if a relevant list is present, every item in the list 
        must be used in the answer.

        The answer will be in two parts, the formatted response answering the question 
        and the citations where you must include the chunks used and detail how they 
        were relevant and how you used them in the answer. You must never overstate 
        the relevance of a chunk or attribute information to them that is not present.
        You should refer to the documents in your answer and advise the user in which 
        documents and in which sections they can find the key details. All answers 
        should be a detailed and forensic representation of the source data. If you 
        cannot answer the question based on the tool results, you should state this 
        clearly and not answer but if possible, you should suggest documents and 
        sections within those documents where the user may be able to find the answer.

        When answering, you should consider the hierachy of the chunks you are reading. 
        Legislation must always be followed by the user, guidance is considered 
        persuasive by courts and should be followed unless there are specific reasons 
        their implementation is not practicable. You should never advise the user in 
        any way."""


def get_embedding_dim(embedding_model):
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=embedding_model).embedding_size


def setup_logging(entry_point: str) -> None:
    date = dt.datetime.today()
    logfile = (
        project_root
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
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["file", "console"],
        },
    }
    logging.config.dictConfig(config)
