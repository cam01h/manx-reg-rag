import pytest
from qdrant_client import QdrantClient, models

from core.sectors import SECTORS_FIELD
from db_ops import verify
from db_ops.utils import build_point_id
from db_ops.verify import (
    check_config,
    check_counts,
    check_ids,
    check_indexes,
    check_payloads,
    check_vectors,
)
from tests.db_ops.verify_helpers import (
    DIM,
    FakeDense,
    FakeSparse,
    fake_client,
    make_chunk,
    make_chunks,
    make_point,
    populate,
)

COLLECTION = "test"


@pytest.fixture
def chunks():
    return make_chunks()


@pytest.fixture
def client(chunks):
    client = QdrantClient(":memory:")
    populate(client, COLLECTION, chunks)
    return client


def text(problems: list[str]) -> str:
    return "\n".join(problems)


# --- counts ---------------------------------------------------------------


def test_counts_match(client, chunks):
    assert check_counts(client, COLLECTION, chunks) == []


def test_a_missing_point_is_reported_with_the_document(client, chunks):
    client.delete(
        COLLECTION,
        models.PointIdsList(points=[build_point_id(chunks[1].chunk_id)]),
    )
    problems = text(check_counts(client, COLLECTION, chunks))
    assert "has [6] points but the chunk jsonl has [7] chunks" in problems
    assert "[Doc A]: jsonl [4] | qdrant [3]" in problems
    assert "Doc B" not in problems


def test_extra_points_that_belong_to_no_document_are_reported(client, chunks):
    client.upsert(
        COLLECTION, [make_point(make_chunk(99, "Gone Doc"), FakeDense(), FakeSparse())]
    )
    problems = text(check_counts(client, COLLECTION, chunks))
    assert "has [8] points but the chunk jsonl has [7] chunks" in problems
    assert "[1] points in qdrant belong to no document in the jsonl" in problems


# --- ids ------------------------------------------------------------------


def test_ids_match(client, chunks):
    assert check_ids(client, COLLECTION, chunks) == []


def test_missing_and_stale_points_are_named(client, chunks):
    client.delete(
        COLLECTION,
        models.PointIdsList(points=[build_point_id(chunks[0].chunk_id)]),
    )
    stale = make_chunk(99, "Gone Doc")
    client.upsert(COLLECTION, [make_point(stale, FakeDense(), FakeSparse())])
    problems = text(check_ids(client, COLLECTION, chunks))
    assert "in the jsonl but not in qdrant (embed them) [1]" in problems
    assert chunks[0].chunk_id in problems
    assert "in qdrant but not in the jsonl (stale) [1]" in problems
    assert stale.chunk_id in problems


# --- payloads -------------------------------------------------------------


def test_payloads_match(client, chunks):
    assert check_payloads(client, COLLECTION, chunks) == []


def test_a_changed_payload_names_the_chunk_and_the_fields(client, chunks):
    client.set_payload(
        COLLECTION,
        payload={"url": "https://example.com/other.pdf", "sectors": ["class_1"]},
        points=[build_point_id(chunks[2].chunk_id)],
    )
    problems = text(check_payloads(client, COLLECTION, chunks))
    assert "payload differs from the jsonl [1]" in problems
    assert chunks[2].chunk_id in problems
    assert "differs in sectors, url" in problems


@pytest.mark.parametrize(
    "changed",
    [
        {"sectors": ["class_1"]},
        {"terms_used": ["customer"]},
        {"hierarchy": "guidance"},
        {"body": "a different body"},
        {"url": "https://example.com/other.pdf"},
        {"headers": ["Part 0", "Extra"]},
    ],
)
def test_a_single_changed_field_is_reported(client, chunks, changed):
    client.set_payload(
        COLLECTION, payload=changed, points=[build_point_id(chunks[0].chunk_id)]
    )
    problems = text(check_payloads(client, COLLECTION, chunks))
    assert f"differs in {next(iter(changed))})" in problems


def test_stale_points_are_left_to_the_id_check(client, chunks):
    client.upsert(
        COLLECTION, [make_point(make_chunk(99, "Gone Doc"), FakeDense(), FakeSparse())]
    )
    assert check_payloads(client, COLLECTION, chunks) == []


# --- config ---------------------------------------------------------------


def test_good_config_passes():
    assert check_config(fake_client(), COLLECTION, DIM) == []


def test_real_collection_vectors_are_read_correctly(client):
    assert check_config(client, COLLECTION, DIM) == []


@pytest.mark.parametrize(
    "client_kwargs, expected",
    [
        ({"size": 384}, "vector size is [384], the embedding model gives [8]"),
        ({"distance": models.Distance.DOT}, "expected cosine"),
        ({"dense_name": "other"}, "no [dense] vector configured"),
        ({"sparse_name": None}, "no [bm25] sparse vector configured"),
        ({"modifier": models.Modifier.NONE}, "expected idf"),
    ],
)
def test_bad_config_is_reported(client_kwargs, expected):
    problems = text(check_config(fake_client(**client_kwargs), COLLECTION, DIM))
    assert expected in problems


def test_a_good_sectors_index_passes():
    assert check_indexes(fake_client(), COLLECTION) == []


@pytest.mark.parametrize(
    "index, expected",
    [
        (None, f"no payload index on [{SECTORS_FIELD}]"),
        (models.PayloadSchemaType.TEXT, "expected keyword"),
    ],
)
def test_a_missing_or_wrong_sectors_index_is_reported(index, expected):
    assert expected in text(check_indexes(fake_client(index=index), COLLECTION))


# --- vectors --------------------------------------------------------------


def test_current_vectors_pass(client, chunks):
    problems, seed = check_vectors(
        client, COLLECTION, chunks, FakeDense(), FakeSparse(), seed=1
    )
    assert problems == []
    assert seed == 1


def test_a_changed_dense_model_is_caught_and_the_seed_is_reported(client, chunks):
    problems, _ = check_vectors(
        client, COLLECTION, chunks, FakeDense("other"), FakeSparse(), seed=7
    )
    joined = text(problems)
    assert "dense vector is stale" in joined
    assert "sparse vector is stale" not in joined
    assert "seed [7]" in joined
    assert "mrr embed --rebuild" in joined


def test_a_changed_sparse_model_is_caught(client, chunks):
    problems, _ = check_vectors(
        client, COLLECTION, chunks, FakeDense(), FakeSparse("other"), seed=7
    )
    joined = text(problems)
    assert "sparse vector is stale" in joined
    assert "dense vector is stale" not in joined


def test_changed_embedding_text_is_caught(client, chunks, monkeypatch):
    monkeypatch.setattr(verify, "build_embedding_text", lambda c: f"changed {c.body}")
    problems, _ = check_vectors(
        client, COLLECTION, chunks, FakeDense(), FakeSparse(), seed=3
    )
    assert "dense vector is stale" in text(problems)


def test_the_same_seed_picks_the_same_chunks(client, chunks):
    kwargs = {
        "dense_model": FakeDense("other"),
        "sparse_model": FakeSparse(),
        "sample_size": 3,
    }
    first, _ = check_vectors(client, COLLECTION, chunks, seed=11, **kwargs)
    again, _ = check_vectors(client, COLLECTION, chunks, seed=11, **kwargs)
    different, _ = check_vectors(client, COLLECTION, chunks, seed=12, **kwargs)
    assert first == again
    assert [p for p in first if "stale" in p] and len(
        [p for p in first if "stale" in p]
    ) == 3
    assert first != different or len(chunks) <= 3


def test_a_sample_larger_than_the_collection_checks_everything(client, chunks):
    problems, _ = check_vectors(
        client,
        COLLECTION,
        chunks,
        FakeDense("other"),
        FakeSparse(),
        sample_size=50,
        seed=1,
    )
    assert len([p for p in problems if "dense vector is stale" in p]) == len(chunks)


def test_a_chunk_with_no_point_is_reported(client, chunks):
    client.delete(
        COLLECTION,
        models.PointIdsList(points=[build_point_id(chunks[0].chunk_id)]),
    )
    problems, _ = check_vectors(
        client, COLLECTION, chunks, FakeDense(), FakeSparse(), sample_size=50, seed=1
    )
    assert f"{chunks[0].chunk_id}: no vectors in qdrant" in problems
