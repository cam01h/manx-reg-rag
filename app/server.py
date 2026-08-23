# setup_logging must run before importing app.llm so the agents init log is caught by the handler
from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from pydantic_ai import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from qdrant_client import QdrantClient
from app.deps import AppDeps
from app.models import ConversationStep, UserPrompt
from config import (
    DENSE_MODEL_NAME,
    QDRANT_URL,
    RERANKING_MODEL_NAME,
    RETRIEVAL_MODE,
    SPARSE_MODEL_NAME,
    setup_logging,
)
from cachetools import TTLCache

setup_logging("app")
import logging  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402
from fastapi import FastAPI, Request  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from app.llm import agent  # noqa: E402
from app.startup_checks import run_startup_checks  # noqa: E402

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


app = FastAPI(lifespan=lifespan)

conversations = TTLCache[str, list[ConversationStep]](maxsize=1000, ttl=3600)


def to_message_history(steps: list[ConversationStep]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for step in steps:
        messages.append(ModelRequest(parts=[UserPromptPart(content=step.user_prompt)]))
        messages.append(ModelResponse(parts=[TextPart(content=step.agent_response)]))
    return messages


@app.post("/query")
async def query(user_prompt: UserPrompt, request: Request):
    logger.info("query received: %s", user_prompt.prompt)
    deps = AppDeps(
        qdrant_client=request.app.state.qdrant_client,
        dense_model=request.app.state.dense_model,
        sparse_model=request.app.state.sparse_model,
        reranker_model=request.app.state.reranker_model,
        mode=request.app.state.mode,
    )
    steps = conversations.get(user_prompt.session_id, [])
    try:
        result = await agent.run(
            user_prompt.prompt,
            message_history=to_message_history(steps),
            deps=deps,
        )
    except Exception:
        logger.exception("agent.run failed during /query")
        raise
    conversations[user_prompt.session_id] = steps + [
        ConversationStep(
            user_prompt=user_prompt.prompt,
            agent_response=result.output.answer,
        )
    ]
    logger.info("query complete")
    logger.debug("model output: %s", result.output.model_dump_json())
    return result.output.model_dump()


@app.post("/reset")
async def reset(user_prompt: UserPrompt):
    n = len(conversations.pop(user_prompt.session_id, []))
    logger.info("conversation reset deleting %d interactions", n)
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="web", html=True), name="web")
