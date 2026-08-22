import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import logging
from pathlib import Path

from fastembed import TextEmbedding
from qdrant_client import QdrantClient

from config import COLLECTION, EMBEDDING_MODEL, PROJECT_ROOT, QDRANT_URL, setup_logging
from db_ops.retrieval import embed_query_text, query_collection, return_payload
from tests.db_ops.query_metrics.query_data import QUERY_TEST_DATA, RetrievalTest

TEST_TOP_N_RESULTS = 1000
CURRENT_CONFIGURATION = "dense_vector_embedding"
RESULTS_DIR = PROJECT_ROOT / "tests/db_ops/query_metrics/data"

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MatchedTestChunk:
    search_term: str
    document: str
    expected_string: str
    chunk_id: str
    rank: int


def build_config(top_n: int) -> dict:
    return {
        "label": CURRENT_CONFIGURATION,
        "embedding_model": EMBEDDING_MODEL,
        "collection": COLLECTION,
        "top_n": top_n,
    }


def run_test_query(
    test: RetrievalTest,
    client: QdrantClient,
    embedding_model: TextEmbedding,
    top_n: int = TEST_TOP_N_RESULTS,
) -> list[MatchedTestChunk]:
    matches: list[MatchedTestChunk] = []

    vector = embed_query_text(test.search_term, embedding_model)
    results = query_collection(vector, client, top_n=top_n)
    chunks = return_payload(results)

    for doc, anchor_string in test.expected_strings:
        match_id = ""
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
    logger.info(f"{test.search_term[:50]}: {found}/{len(matches)} found")
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
        / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S}_{config['label']}.json"
    )
    path.write_text(json.dumps(payload, indent=2))
    return path


def main():
    client = QdrantClient(url=QDRANT_URL)
    model = TextEmbedding(EMBEDDING_MODEL)
    config = build_config(TEST_TOP_N_RESULTS)

    logger.info("starting query metrics test")
    matches = [
        m
        for test in QUERY_TEST_DATA
        for m in run_test_query(test, client, model, TEST_TOP_N_RESULTS)
    ]

    path = write_results(matches, config)
    logger.info(
        f"{len(matches)} targets, {sum(m.rank > 0 for m in matches)} found -> {path}"
    )


if __name__ == "__main__":
    setup_logging("query metrics")
    main()
