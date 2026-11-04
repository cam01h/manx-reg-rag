import asyncio
import json
from dataclasses import asdict

import pytest
from qdrant_client import QdrantClient, models

from app.startup_checks import check_index_matches_data
from config import COLLECTION
from db_ops.utils import build_point_id
from tests.db_ops.verify_helpers import DIM, make_chunks, populate


@pytest.fixture
def chunk_dir(tmp_path):
    directory = tmp_path / "chunks"
    directory.mkdir()
    chunks = make_chunks()
    for document in {c.document for c in chunks}:
        lines = [json.dumps(asdict(c)) for c in chunks if c.document == document]
        (directory / f"{document}.jsonl").write_text("\n".join(lines) + "\n")
    return directory


@pytest.fixture
def client():
    client = QdrantClient(":memory:")
    populate(client, COLLECTION, make_chunks())
    return client


def run_check(client, chunk_dir, dense_size=DIM):
    asyncio.run(
        check_index_matches_data(dense_size, client=client, chunk_dir=chunk_dir)
    )


def test_a_matching_collection_starts_and_a_missing_index_only_warns(
    client, chunk_dir, caplog
):
    # the in-memory client never has a payload index, which makes it a handy "missing index"
    run_check(client, chunk_dir)
    assert "no payload index on" in caplog.text


def test_a_missing_point_stops_startup_and_says_to_embed(client, chunk_dir, caplog):
    chunk = make_chunks()[0]
    client.delete(
        COLLECTION, models.PointIdsList(points=[build_point_id(chunk.chunk_id)])
    )
    with pytest.raises(RuntimeError, match="run mrr embed"):
        run_check(client, chunk_dir)
    assert "[Doc A]: jsonl [4] | qdrant [3]" in caplog.text


def test_a_config_mismatch_stops_startup(client, chunk_dir):
    # the collection holds 8-wide dense vectors, the model says 1024
    with pytest.raises(RuntimeError, match="run mrr embed"):
        run_check(client, chunk_dir, dense_size=1024)
