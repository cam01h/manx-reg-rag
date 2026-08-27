from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient
from app.startup_checks import run_startup_checks
from config import (
    DENSE_MODEL_NAME,
    QDRANT_URL,
    RERANKING_MODEL_NAME,
    RETRIEVAL_MODE,
    SPARSE_MODEL_NAME,
)
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting %s", app.title)
    app.state.qdrant_client = QdrantClient(url=QDRANT_URL)
    app.state.dense_model = TextEmbedding(model_name=DENSE_MODEL_NAME)
    app.state.sparse_model = SparseTextEmbedding(SPARSE_MODEL_NAME)
    app.state.reranker_model = TextCrossEncoder(model_name=RERANKING_MODEL_NAME)
    app.state.mode = RETRIEVAL_MODE
    await run_startup_checks()
    yield
    app.state.qdrant_client.close()
