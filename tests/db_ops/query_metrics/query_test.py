import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import logging
from pathlib import Path

from fastembed import SparseTextEmbedding, TextEmbedding
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient

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
    embed_query_dense,
    embed_query_sparse,
    query_collection,
    rerank_chunks,
    return_payload,
)
from tests.db_ops.query_metrics.query_data import QUERY_TEST_DATA, RetrievalTest

TEST_TOP_N_RESULTS = 50
TEST_RERANKED_N_RESULTS = 10
RERANK_IN_TESTS = True
CURRENT_CONFIGURATION = (
    f"large_model-{'reranked-jina' if RERANK_IN_TESTS else 'no_reranker'}"
)
RESULTS_DIR = PROJECT_ROOT / "tests/db_ops/query_metrics/data"
TEST_MODES = ("dense", "sparse", "hybrid")

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MatchedTestChunk:
    search_term: str
    document: str
    expected_string: str
    chunk_id: str
    rank: int


def build_config(top_n: int, mode: str) -> dict:
    return {
        "label": f"{CURRENT_CONFIGURATION}-{mode}",
        "dense_model": DENSE_MODEL_NAME,
        "sparse_model": SPARSE_MODEL_NAME,
        "collection": COLLECTION,
        "reranked": RERANK_IN_TESTS,
        "reranking model": RERANKING_MODEL_NAME,
        "retrieval_mode": mode,
        "top_n": top_n,
    }


def run_test_query(
    test: RetrievalTest,
    client: QdrantClient,
    dense_model: TextEmbedding,
    sparse_model: SparseTextEmbedding,
    reranking_model: TextCrossEncoder,
    top_n: int = TEST_TOP_N_RESULTS,
    mode: str = RETRIEVAL_MODE,
) -> list[MatchedTestChunk]:
    matches: list[MatchedTestChunk] = []

    dense_vector = embed_query_dense(test.search_term, dense_model)
    sparse_vector = embed_query_sparse(test.search_term, sparse_model)
    results = query_collection(
        dense_vector, sparse_vector, client, mode=mode, seen=set()
    )
    chunks = return_payload(results)
    if RERANK_IN_TESTS:
        chunks = rerank_chunks(test.search_term, chunks, reranking_model)

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
            )
        )
    found = sum(m.rank > 0 for m in matches)
    logger.debug(f"{test.search_term[:50]}: {found}/{len(matches)} found")
    return matches


def write_results(matches: list[MatchedTestChunk], config: dict) -> Path:
    payload = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "results": [asdict(m) for m in matches],
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = (
        RESULTS_DIR
        / f"{datetime.now(timezone.utc):%Y-%m-%d_%H-%M}_{config['label']}.json"
    )
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


def main(mode: str = RETRIEVAL_MODE):
    client = QdrantClient(url=QDRANT_URL)
    dense_model = TextEmbedding(DENSE_MODEL_NAME)
    sparse_model = SparseTextEmbedding(SPARSE_MODEL_NAME)
    reranking_model = TextCrossEncoder(RERANKING_MODEL_NAME)

    logger.info("starting query metrics test [%s]", mode)
    config = build_config(TEST_TOP_N_RESULTS, mode)
    matches = [
        m
        for test in QUERY_TEST_DATA
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
    logger.info(
        f"[{mode}] {len(matches)} targets, "
        f"{sum(m.rank > 0 for m in matches)} found -> {path}"
    )


if __name__ == "__main__":
    setup_logging("query metrics")
    args = parse_args()
    main(args.mode)
