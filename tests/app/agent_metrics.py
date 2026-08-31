import asyncio
import logfire
from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from pydantic_ai import Agent, AgentRunResult, ToolReturnPart
from qdrant_client import QdrantClient
from app.models import AgentResponse
from config import (
    FINAL_RETURN_TOP_N,
    MODEL,
    PRE_RERANK_POOL,
    PROJECT_ROOT,
    QDRANT_URL,
    REASONING_EFFORT,
    DENSE_MODEL_NAME,
    SPARSE_MODEL_NAME,
    RERANKING_MODEL_NAME,
    RETRIEVAL_MODE,
)
from app.llm import agent
from app.deps import AppDeps


RUNS_PER_QUERY = 3
AGENT_HARNESS = "default pydantic"
JUDGE_MODEL = "deepseek-v4-flash"
AGENT_TEST_RESULTS_DIR = PROJECT_ROOT / "tests/app/agent_metrics/data"
TEST_MODE = "anchor judge and grounding judge"
LABEL = f"{AGENT_HARNESS}-{MODEL}"


def build_deps() -> AppDeps:
    return AppDeps(
        qdrant_client=QdrantClient(url=QDRANT_URL),
        dense_model=TextEmbedding(DENSE_MODEL_NAME),
        sparse_model=SparseTextEmbedding(SPARSE_MODEL_NAME),
        reranker_model=TextCrossEncoder(RERANKING_MODEL_NAME),
        mode=RETRIEVAL_MODE,
    )


def build_config() -> dict:
    return {
        "label": LABEL,
        "model": MODEL,
        "reasoning effort": REASONING_EFFORT,
        "agent harness": AGENT_HARNESS,
        "test mode": TEST_MODE,
        "judge model": JUDGE_MODEL,
        "runs per query": RUNS_PER_QUERY,
        "retrieval mode": RETRIEVAL_MODE,
        "pre-rerank pool": PRE_RERANK_POOL,
        "final top n": FINAL_RETURN_TOP_N,
    }


# TODO: Run inside the test loop so second run doesnt inherit seen chunk
# exclusions from previous runs
async def run_agent_as_test_case(
    test_agent: Agent[AppDeps, AgentResponse], prompt: str, deps: AppDeps
) -> AgentRunResult[AgentResponse]:
    try:
        result = await test_agent.run(user_prompt=prompt, deps=deps)
    except Exception as e:
        raise RuntimeError(f"failed query: [{prompt}]") from e
    return result


def extract_chunks_served(result: AgentRunResult[AgentResponse]):
    return [
        part
        for message in result.all_messages()
        for part in message.parts
        if isinstance(part, ToolReturnPart)
    ]


def build_tool_records():
    """build a tool call record for each tool call"""
    pass


def run_anchor_judge():
    pass


def run_grounding_judge():
    pass


def build_result():
    """use the judge responses to build the RunResult"""
    pass


def write_results():
    pass


async def main():
    deps = build_deps()
    result = await run_agent_as_test_case(
        agent, "what is a commercially exposed person?", deps
    )

    for message in result.all_messages():
        for part in message.parts:
            print(type(part).__name__)
            print(repr(part))
            print("---")


if __name__ == "__main__":
    logfire.configure()
    asyncio.run(main())
