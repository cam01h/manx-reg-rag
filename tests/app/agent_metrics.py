import asyncio
from dataclasses import asdict
from pathlib import Path
from typing import cast
import logfire
import time
from datetime import datetime, timezone
import json
from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from pydantic_ai import Agent, AgentRunResult, ToolCallPart, ToolReturnPart
from qdrant_client import QdrantClient
from app.models import AgentResponse
from tests.app.judge import grounding_judge, anchor_judge, JUDGE_MODEL
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
    setup_logging,
)
from app.llm import agent
from app.deps import AppDeps
from db_ops.models import ServedPayload
from tests.app.agent_metrics_test_data import AGENT_TEST_DATA
from tests.app.models import (
    AgentTest,
    Anchor,
    AnchorJudgement,
    AnchorResult,
    GroundingJudgement,
    RunResult,
    ToolCallRecord,
)
import logging

logger = logging.getLogger(__name__)


RUNS_PER_QUERY = 3
AGENT_HARNESS = "default pydantic"
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


async def run_agent_as_test_case(
    test_agent: Agent[AppDeps, AgentResponse], prompt: str, deps: AppDeps
) -> AgentRunResult[AgentResponse]:
    try:
        result = await test_agent.run(user_prompt=prompt, deps=deps)
    except Exception as e:
        raise RuntimeError(f"failed query: [{prompt}]") from e
    return result


def get_tool_returns(result: AgentRunResult[AgentResponse]) -> list[ToolReturnPart]:
    return [
        part
        for message in result.all_messages()
        for part in message.parts
        if isinstance(part, ToolReturnPart)
    ]


def extract_chunks_served(tool_returns: list[ToolReturnPart]) -> list[ServedPayload]:
    return [
        chunk
        for part in tool_returns
        if part.tool_name != "final_result"
        for chunk in cast(tuple[list[ServedPayload], list], part.content)[0]
    ]


def get_tool_calls(result: AgentRunResult[AgentResponse]) -> list[ToolCallPart]:
    return [
        part
        for message in result.all_messages()
        for part in message.parts
        if isinstance(part, ToolCallPart)
    ]


def build_tool_records(
    tool_calls: list[ToolCallPart],
    tool_returns: list[ToolReturnPart],
) -> list[ToolCallRecord]:
    returns = {part.tool_call_id: part for part in tool_returns}

    records: list[ToolCallRecord] = []
    for call in tool_calls:
        if call.tool_name == "final_result":
            continue

        return_part = returns[call.tool_call_id]
        chunks = cast(tuple[list[ServedPayload], list], return_part.content)[0]

        records.append(
            ToolCallRecord(
                tool_name=call.tool_name,
                query=call.args_as_dict()["query"],
                chunk_ids=tuple(chunk.title for chunk in chunks),
            )
        )
    return records


def match_anchors(
    test: AgentTest,
    chunks: list[ServedPayload],
) -> list[tuple[Anchor, ServedPayload | None]]:
    matches = []
    for anchor in test.anchors:
        found = None
        for chunk in chunks:
            document = chunk.title.split("\n")[0]
            if document == anchor.document and anchor.text in chunk.body:
                found = chunk
                break
        matches.append((anchor, found))
    return matches


async def run_anchor_judge(
    anchor: Anchor,
    chunk: ServedPayload,
    answer: str,
) -> AnchorJudgement:
    prompt = (
        f"<source_extract>\n{chunk.title}\n\n{chunk.body}\n</source_extract>\n\n"
        f"<answer>\n{answer}\n</answer>"
    )
    result = await anchor_judge.run(prompt)
    return result.output


async def build_anchor_results(
    matches: list[tuple[Anchor, ServedPayload | None]],
    answer: str,
) -> list[AnchorResult]:
    results: list[AnchorResult] = []
    for anchor, chunk in matches:
        if chunk is None:
            results.append(
                AnchorResult(
                    document=anchor.document,
                    text=anchor.text,
                    retrieved=False,
                    content_present=None,
                    reasoning="anchor not retrieved",
                )
            )
            continue

        judgement = await run_anchor_judge(anchor, chunk, answer)
        results.append(
            AnchorResult(
                document=anchor.document,
                text=anchor.text,
                retrieved=True,
                content_present=judgement.content_present,
                reasoning=judgement.reasoning,
            )
        )
    return results


async def run_grounding_judge(
    chunks: list[ServedPayload],
    answer: str,
) -> GroundingJudgement:
    sources = "\n\n---\n\n".join(f"{chunk.title}\n\n{chunk.body}" for chunk in chunks)
    prompt = (
        f"<source_extracts>\n{sources}\n</source_extracts>\n\n"
        f"<answer>\n{answer}\n</answer>"
    )
    result = await grounding_judge.run(prompt)
    return result.output


async def run_test_case(
    test: AgentTest,
    run_index: int,
    deps: AppDeps,
) -> RunResult:
    start = time.perf_counter()
    result = await run_agent_as_test_case(agent, test.question, deps)
    elapsed = time.perf_counter() - start

    tool_calls = get_tool_calls(result)
    tool_returns = get_tool_returns(result)
    chunks = extract_chunks_served(tool_returns)

    records = build_tool_records(tool_calls, tool_returns)
    matches = match_anchors(test, chunks)

    answer = result.output.answer
    anchors = await build_anchor_results(matches, answer)
    grounding = await run_grounding_judge(chunks, answer)

    return build_result(
        test, run_index, result, answer, anchors, grounding, records, elapsed
    )


def build_result(
    test: AgentTest,
    run_index: int,
    result: AgentRunResult[AgentResponse],
    answer: str,
    anchors: list[AnchorResult],
    grounding: GroundingJudgement,
    records: list[ToolCallRecord],
    elapsed: float,
) -> RunResult:
    usage = result.usage()
    return RunResult(
        question=test.question,
        run_index=run_index,
        answer=answer,
        anchors=tuple(anchors),
        grounding=grounding,
        tool_calls=tuple(records),
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        elapsed=elapsed,
    )


def result_to_dict(result: RunResult) -> dict:
    data = asdict(result)
    data["grounding"] = result.grounding.model_dump()
    for anchor_data, anchor in zip(data["anchors"], result.anchors):
        anchor_data["classification"] = anchor.classification()
    return data


def write_results(results: list[RunResult], config: dict) -> Path:
    payload = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "results": [result_to_dict(r) for r in results],
    }

    AGENT_TEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = (
        AGENT_TEST_RESULTS_DIR
        / f"{datetime.now(timezone.utc):%Y-%m-%d_%H-%M}_{config['label']}.json"
    )
    path.write_text(json.dumps(payload, indent=2))
    return path


async def main():
    config = build_config()
    results: list[RunResult] = []

    for test in AGENT_TEST_DATA[:1]:
        for run_index in range(RUNS_PER_QUERY):
            deps = build_deps()
            result = await run_test_case(test, run_index, deps)
            results.append(result)
            logger.info(
                "%s run %d: %d/%d anchors retrieved",
                test.question[:50],
                run_index,
                sum(a.retrieved for a in result.anchors),
                len(result.anchors),
            )

    path = write_results(results, config)
    logger.info("%d runs -> %s", len(results), path)


if __name__ == "__main__":
    setup_logging("agent metrics")
    logfire.configure(send_to_logfire=False)
    asyncio.run(main())
