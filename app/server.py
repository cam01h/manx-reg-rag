from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app.llm import agent
from config import setup_logging
import logging

setup_logging("app")
logger = logging.getLogger(__name__)

app = FastAPI()

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
