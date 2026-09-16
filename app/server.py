# setup_logging and configure_logfire must run before importing
# app.llm so the agents init log is caught by the handler
import logfire
from app.deps import AppDeps
from app.lifespan import lifespan
from app.models import ConversationStep, UserPrompt
from app.observabilty import configure_logfire
from app.sessions import CONVERSATIONS, to_message_history
from config import (
    setup_logging,
)
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
import logging

setup_logging("app")
configure_logfire()

from app.llm import agent  # noqa: E402

logger = logging.getLogger(__name__)


app = FastAPI(lifespan=lifespan)

logfire.instrument_fastapi(app)

ACCESS_EMAIL_HEADER = "Cf-Access-Authenticated-User-Email"


def session_key(user_prompt: UserPrompt, request: Request) -> str:
    return request.headers.get(ACCESS_EMAIL_HEADER) or user_prompt.session_id


@app.post("/query")
async def query(user_prompt: UserPrompt, request: Request):
    key = session_key(user_prompt, request)
    logger.info("query received [%s]: [%s]", key, user_prompt.prompt)
    deps = AppDeps(
        qdrant_client=request.app.state.qdrant_client,
        dense_model=request.app.state.dense_model,
        sparse_model=request.app.state.sparse_model,
        reranker_model=request.app.state.reranker_model,
        mode=request.app.state.mode,
    )
    steps = CONVERSATIONS.get(key, [])
    try:
        result = await agent.run(
            user_prompt.prompt,
            message_history=to_message_history(steps),
            deps=deps,
        )
    except Exception:
        logger.exception("agent.run failed during /query")
        raise
    CONVERSATIONS[key] = steps + [
        ConversationStep(
            user_prompt=user_prompt.prompt,
            agent_response=result.output.answer,
        )
    ]
    logger.info("query complete")
    logger.debug("model output: %s", result.output.model_dump_json())
    return result.output.model_dump()


@app.post("/reset")
async def reset(user_prompt: UserPrompt, request: Request):
    key = session_key(user_prompt, request)
    n = len(CONVERSATIONS.pop(key, []))
    logger.info("conversation reset [%s] deleting %d interactions", key, n)
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="web", html=True), name="web")
