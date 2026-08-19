# setup_logging must run before importing app.llm so the agents init log is caught by the handler
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from app.deps import AppDeps
from app.models import UserPrompt
from config import EMBEDDING_MODEL, QDRANT_URL, setup_logging

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
    app.state.embedding_model = TextEmbedding(model_name=EMBEDDING_MODEL)
    await run_startup_checks()
    yield
    app.state.qdrant_client.close()


app = FastAPI(lifespan=lifespan)

conversation = []


@app.post("/query")
async def query(user_prompt: UserPrompt, request: Request):
    global conversation
    logger.info("query received: %s", user_prompt.prompt)
    deps = AppDeps(
        qdrant_client=request.app.state.qdrant_client,
        embedding_model=request.app.state.embedding_model,
    )
    try:
        result = await agent.run(
            user_prompt.prompt, message_history=conversation, deps=deps
        )
    except Exception:
        logger.exception("agent.run failed during /query")
        raise
    conversation = result.all_messages()
    logger.info("query complete")
    logger.debug("model output: %s", result.output.model_dump_json())
    return result.output.model_dump()


@app.post("/reset")
async def reset():
    global conversation
    n = len(conversation)
    conversation = []
    logger.info("conversation reset deleting %d interactions", n)
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="web", html=True), name="web")
