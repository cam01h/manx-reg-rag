from pydantic import BaseModel
from pydantic_ai import Agent
from config import MODEL, SYSTEM_PROMPT
from db_ops.retrieval import get_chunks_with_definitions
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()


class Citation(BaseModel):
    chunk_id: str
    relevance: str


class AgentResponse(BaseModel):
    answer: str
    citations: list[Citation]


agent = Agent(
    MODEL,
    instructions=SYSTEM_PROMPT,
    output_type=AgentResponse,
    tools=[get_chunks_with_definitions],
)
logger.info("agent initialised with model name: %s", MODEL)
