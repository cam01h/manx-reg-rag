# setup_logging must run before importing app.llm so the agents init log is caught by the handler
from config import setup_logging

setup_logging("app")
import logging  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402
from app.llm import agent  # noqa: E402
from app.startup_checks import run_startup_checks  # noqa: E402

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting %s", app.title)
    await run_startup_checks()
    yield


app = FastAPI(lifespan=lifespan)

conversation = []


class QueryRequest(BaseModel):
    prompt: str


@app.post("/query")
async def query(request: QueryRequest):
    global conversation
    logger.info("query received: %s", request.prompt)
    try:
        result = await agent.run(request.prompt, message_history=conversation)
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
