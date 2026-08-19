from pydantic_ai import Agent
from app.deps import AppDeps
from app.models import AgentResponse
from config import MODEL, SYSTEM_PROMPT
from db_ops.retrieval import get_chunks_with_definitions
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()


agent = Agent(
    MODEL,
    instructions=SYSTEM_PROMPT,
    output_type=AgentResponse,
    tools=[get_chunks_with_definitions],
    deps_type=AppDeps,
)
logger.info("agent initialised with model name: %s", MODEL)
