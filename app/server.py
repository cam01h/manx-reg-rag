# setup_logging must run before importing app.llm so the agents init log is caught by the handler
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
from app.llm import agent

setup_logging("app")
import logging  # noqa: E402

logger = logging.getLogger(__name__)


app = FastAPI(lifespan=lifespan)

configure_logfire()
logfire.instrument_fastapi(app)


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
    steps = CONVERSATIONS.get(user_prompt.session_id, [])
    try:
        result = await agent.run(
            user_prompt.prompt,
            message_history=to_message_history(steps),
            deps=deps,
        )
    except Exception:
        logger.exception("agent.run failed during /query")
        raise
    CONVERSATIONS[user_prompt.session_id] = steps + [
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
    n = len(CONVERSATIONS.pop(user_prompt.session_id, []))
    logger.info("conversation reset deleting %d interactions", n)
    return {"status": "ok"}


app.mount("/", StaticFiles(directory="web", html=True), name="web")
