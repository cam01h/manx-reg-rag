import argparse
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient
from tqdm import tqdm

from config import (
    COLLECTION,
    DENSE_MODEL_NAME,
    PROJECT_ROOT,
    QDRANT_URL,
    RERANKING_MODEL_NAME,
    RETRIEVAL_MODE,
    SPARSE_MODEL_NAME,
    setup_logging,
)
from db_ops.retrieval import (
    query_collection,
    rerank_chunks,
    return_payload,
)
from db_ops.utils import build_dense_vector, build_sparse_vector
from tests.db_ops.query_metrics.query_data import QUERY_TEST_DATA, RetrievalTest

TEST_TOP_N_RESULTS = 50
TEST_RERANKED_N_RESULTS = 10
RERANK_IN_TESTS = True
CURRENT_CONFIGURATION = (
    f"large_model-{'reranked-jina' if RERANK_IN_TESTS else 'no_reranker'}"
)
RESULTS_DIR = PROJECT_ROOT / "tests/db_ops/query_metrics/data"
TEST_MODES = ("dense", "sparse", "hybrid")

SUMMARY_TOP_NS = [5, 10, 20, 50]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MatchedTestChunk:
    search_term: str
    document: str
    expected_string: str
    chunk_id: str
    rank: int
    time: float


def build_config(top_n: int, mode: str) -> dict[str, str | int]:
    return {
        "label": f"{CURRENT_CONFIGURATION}-{mode}",
        "dense_model": DENSE_MODEL_NAME,
        "sparse_model": SPARSE_MODEL_NAME,
        "collection": COLLECTION,
        "reranked": RERANK_IN_TESTS,
        "reranking model": RERANKING_MODEL_NAME,
        "total test searches": len(QUERY_TEST_DATA),
        "total expected strings": sum(
            len(test.expected_strings) for test in QUERY_TEST_DATA
        ),
        "retrieval_mode": mode,
        "top_n": top_n,
    }


def run_test_query(
    test: RetrievalTest,
    client: QdrantClient,
    dense_model: TextEmbedding,
    sparse_model: SparseTextEmbedding,
    reranking_model: TextCrossEncoder | None,
    top_n: int = TEST_TOP_N_RESULTS,
    mode: str = RETRIEVAL_MODE,
) -> list[MatchedTestChunk]:
    matches: list[MatchedTestChunk] = []

    start = time.perf_counter()

    dense_vector = build_dense_vector(test.search_term, dense_model)
    sparse_vector = build_sparse_vector(test.search_term, sparse_model)
    results = query_collection(
        dense_vector, sparse_vector, client, mode=mode, seen=set(), sectors=()
    )

    chunks = return_payload(results)
    if reranking_model:
        chunks = rerank_chunks(test.search_term, chunks, reranking_model)

    elapsed = time.perf_counter() - start

    for doc, anchor_string in test.expected_strings:
        match_id = ""
        # zero used as not found rather than a new var
        match_rank = 0
        for i, chunk in enumerate(chunks):
            if chunk.document == doc and anchor_string in chunk.body:
                match_id = chunk.chunk_id
                match_rank = i + 1
                break
        matches.append(
            MatchedTestChunk(
                search_term=test.search_term,
                document=doc,
                expected_string=anchor_string,
                chunk_id=match_id,
                rank=match_rank,
                time=elapsed,
            )
        )
    found = sum(m.rank > 0 for m in matches)
    logger.debug(f"{test.search_term[:50]}: {found}/{len(matches)} found")
    return matches


def write_results(matches: list[MatchedTestChunk], config: dict) -> Path:
    payload = {
        "run_at": datetime.now(UTC).isoformat(),
        "config": config,
        "results": [asdict(m) for m in matches],
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{datetime.now(UTC):%Y-%m-%d_%H-%M}_{config['label']}.json"
    path.write_text(json.dumps(payload, indent=2))
    return path


def parse_args():
    parser = argparse.ArgumentParser(description="run retrieval metrics")
    parser.add_argument(
        "--mode",
        choices=TEST_MODES,
        default=RETRIEVAL_MODE,
        help="retrieval mode to test",
    )
    return parser.parse_args()


def build_summary(matches: list[MatchedTestChunk]) -> dict:
    total = len(matches)
    failures = [m for m in matches if m.rank == 0]
    for m in failures:
        logger.warning(
            "failed retrieval: [%s] did not find [%s] in [%s]",
            m.search_term[:60],
            m.expected_string[:60],
            m.document,
        )

    in_top: dict[int, int] = {}
    for top_n in SUMMARY_TOP_NS:
        in_top[top_n] = sum(0 < m.rank <= top_n for m in matches)
        logger.info(
            "expected strings in top [%d]: [%d/%d] [%.1f%%]",
            top_n,
            in_top[top_n],
            total,
            in_top[top_n] / total * 100,
        )

    times = list({m.search_term: m.time for m in matches}.values())
    avg_time = sum(times) / len(times) if times else 0.0
    max_time = max(times, default=0.0)
    fastest_time = min(times, default=0.0)

    return {
        "total_tests": len(QUERY_TEST_DATA),
        "total_expected_strings": total,
        "times": {
            "fastest": fastest_time,
            "max time": max_time,
            "average time": avg_time,
        },
        "in_top": in_top,
        "failures": [
            {
                "search_term": m.search_term,
                "document": m.document,
                "expected_string": m.expected_string,
            }
            for m in failures
        ],
    }


def write_summary(config, matches: list[MatchedTestChunk]) -> None:
    payload = {
        "run_at": datetime.now(UTC).isoformat(),
        "config": config,
        "summary": build_summary(matches),
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = (
        RESULTS_DIR
        / f"{datetime.now(UTC):%Y-%m-%d_%H-%M}_{config['label']}_summary.json"
    )
    path.write_text(json.dumps(payload, indent=2))


def main(mode: str = RETRIEVAL_MODE):
    client = QdrantClient(url=QDRANT_URL)
    dense_model = TextEmbedding(DENSE_MODEL_NAME)
    sparse_model = SparseTextEmbedding(SPARSE_MODEL_NAME)
    reranking_model = (
        TextCrossEncoder(RERANKING_MODEL_NAME) if RERANK_IN_TESTS else None
    )

    logger.info("starting query metrics test [%s]", mode)
    config = build_config(TEST_TOP_N_RESULTS, mode)
    matches = [
        m
        for test in tqdm(QUERY_TEST_DATA, desc=f"querying [{mode}]")
        for m in run_test_query(
            test,
            client,
            dense_model,
            sparse_model,
            reranking_model,
            TEST_TOP_N_RESULTS,
            mode,
        )
    ]
    path = write_results(matches, config)
    write_summary(config, matches)
    logger.info(
        f"[{mode}] {len(matches)} targets, "
        f"{sum(m.rank > 0 for m in matches)} found -> {path}"
    )


if __name__ == "__main__":
    setup_logging("query metrics")
    args = parse_args()
    main(args.mode)
