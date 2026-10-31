import logging
from typing import cast

import logfire
from fastapi import FastAPI, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent
from fastapi.staticfiles import StaticFiles
from pydantic_ai import (
    AgentRunResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ToolReturnPart,
)

from app.deps import AppDeps
from app.lifespan import lifespan
from app.models import ConversationStep, DocumentInfo, UserPrompt
from app.observabilty import configure_logfire
from app.sessions import (
    CONVERSATIONS,
    build_prompt_with_sectors,
    to_message_history,
)
from app.sse import ReadProgress, SearchProgress
from config import (
    setup_logging,
)
from core.sectors import SECTOR_LABELS
from db_ops.models import ServedPayload

setup_logging("app")
configure_logfire()

# setup_logging and configure_logfire must run before importing
# app.llm so the agents init log is caught by the handler
from app.llm import agent

logger = logging.getLogger(__name__)


app = FastAPI(lifespan=lifespan)

logfire.instrument_fastapi(app)

ACCESS_EMAIL_HEADER = "Cf-Access-Authenticated-User-Email"


def session_key(user_prompt: UserPrompt, request: Request) -> str:
    return request.headers.get(ACCESS_EMAIL_HEADER) or user_prompt.session_id


@app.post("/query", response_class=EventSourceResponse)
async def query(user_prompt: UserPrompt, request: Request):
    key = session_key(user_prompt, request)
    logger.info("query received [%s]: [%s]", key, user_prompt.prompt)
    deps = AppDeps(
        qdrant_client=request.app.state.qdrant_client,
        dense_model=request.app.state.dense_model,
        sparse_model=request.app.state.sparse_model,
        reranker_model=request.app.state.reranker_model,
        mode=request.app.state.mode,
        sectors=user_prompt.sectors,
    )
    steps = CONVERSATIONS.get(key, [])
    prompt = build_prompt_with_sectors(user_prompt)
    try:
        async with agent.run_stream_events(
            prompt,
            message_history=to_message_history(steps),
            deps=deps,
        ) as events:
            async for event in events:
                if isinstance(event, FunctionToolCallEvent):
                    term = event.part.args_as_dict().get("query")
                    if term:
                        yield ServerSentEvent(
                            event="search", data=SearchProgress(term=term)
                        )
                elif isinstance(event, FunctionToolResultEvent) and isinstance(
                    event.part, ToolReturnPart
                ):
                    chunks = cast(tuple[list[ServedPayload], list], event.part.content)[
                        0
                    ]
                    for chunk in chunks:
                        document, headers = chunk.title.split("\n", 1)
                        yield ServerSentEvent(
                            event="read",
                            data=ReadProgress(document=document, headers=headers),
                        )
                elif isinstance(event, AgentRunResultEvent):
                    output = event.result.output
                    CONVERSATIONS[key] = steps + [
                        ConversationStep(
                            user_prompt=prompt, agent_response=output.answer
                        )
                    ]
                    logger.info("query complete")
                    logger.debug("model output: %s", output.model_dump_json())
                    yield ServerSentEvent(event="answer", data=output)
    except Exception:
        logger.exception("agent.run failed during /query")
        yield ServerSentEvent(event="error", data="query failed")


@app.post("/reset")
async def reset(user_prompt: UserPrompt, request: Request):
    key = session_key(user_prompt, request)
    n = len(CONVERSATIONS.pop(key, []))
    logger.info("conversation reset [%s] deleting %d interactions", key, n)
    return {"status": "ok"}


@app.get("/documents")
async def get_documents(request: Request) -> list[DocumentInfo]:
    return request.app.state.documents


@app.get("/sectors")
async def get_sectors() -> dict[str, str]:
    return SECTOR_LABELS


app.mount("/", StaticFiles(directory="web", html=True), name="web")
