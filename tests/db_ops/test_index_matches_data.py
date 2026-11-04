"""Checks the real Qdrant collection against the chunk jsonl in data/processed/.

These need a running Qdrant with the collection embedded, so they are marked
`qdrant` and skipped by default. Run them after an embed, on the machine whose
Qdrant you want to check:

    pytest -m qdrant                       # all of them
    VERIFY_SEED=123 pytest -m qdrant -k vectors   # repeat a vector sample

They skip themselves when Qdrant is unreachable or the collection does not exist.
The logic lives in db_ops/verify.py, which is tested without a server in
test_verify.py.
"""

import os

import pytest
from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import QdrantClient

from config import (
    CHUNKS_DIR,
    COLLECTION,
    DENSE_MODEL_NAME,
    QDRANT_URL,
    SPARSE_MODEL_NAME,
)
from db_ops.utils import load_jsonl_dir
from db_ops.verify import (
    check_config,
    check_counts,
    check_ids,
    check_indexes,
    check_payloads,
    check_vectors,
)
from extraction_ops.models import Chunk

pytestmark = pytest.mark.qdrant

EMBED_HINT = "run mrr embed"


def fail_if(problems: list[str], hint: str) -> None:
    if problems:
        pytest.fail("\n".join([*problems, hint]), pytrace=False)


@pytest.fixture(scope="module")
def client() -> QdrantClient:
    client = QdrantClient(url=QDRANT_URL, timeout=30)
    try:
        exists = client.collection_exists(COLLECTION)
    except Exception as e:  # noqa: BLE001 - any connection failure means skip
        pytest.skip(f"qdrant not reachable at {QDRANT_URL}: {e}")
    if not exists:
        pytest.skip(f"collection [{COLLECTION}] does not exist at {QDRANT_URL}")
    return client


@pytest.fixture(scope="module")
def chunks() -> list[Chunk]:
    return load_jsonl_dir(CHUNKS_DIR, Chunk)


def test_point_count_matches_the_jsonl(client, chunks):
    fail_if(check_counts(client, COLLECTION, chunks), EMBED_HINT)


def test_collection_config_is_as_expected(client):
    sizes = {m["model"]: m["dim"] for m in TextEmbedding.list_supported_models()}
    if DENSE_MODEL_NAME not in sizes:
        pytest.skip(f"fastembed does not list the size of [{DENSE_MODEL_NAME}]")
    fail_if(
        check_config(client, COLLECTION, sizes[DENSE_MODEL_NAME]),
        "run mrr embed --rebuild",
    )


def test_sectors_payload_index_exists(client):
    fail_if(
        check_indexes(client, COLLECTION),
        "create the index (see docs/running_the_cli.md)",
    )


def test_every_chunk_has_a_point_and_every_point_a_chunk(client, chunks):
    fail_if(check_ids(client, COLLECTION, chunks), EMBED_HINT)


def test_every_payload_matches_its_chunk(client, chunks):
    fail_if(check_payloads(client, COLLECTION, chunks), EMBED_HINT)


def test_stored_vectors_match_a_fresh_embedding_of_random_chunks(client, chunks):
    seed = int(os.environ["VERIFY_SEED"]) if "VERIFY_SEED" in os.environ else None
    problems, _ = check_vectors(
        client,
        COLLECTION,
        chunks,
        TextEmbedding(DENSE_MODEL_NAME),
        SparseTextEmbedding(SPARSE_MODEL_NAME),
        seed=seed,
    )
    fail_if(problems, "")
