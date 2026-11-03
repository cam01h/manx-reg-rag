import json
from pathlib import Path

import pytest

from extraction_ops import TOOLBELT_REGISTRY
from extraction_ops.jsonl_stats import build_golden, compare, save_golden


def make_chunk(i: int, body_len: int = 100, **overrides) -> dict:
    chunk = {
        "chunk_id": f"Doc, Part {i} - hash{i:04d}",
        "document": "Doc",
        "hierarchy": "primary legislation",
        "sectors": ["class_1", "class_2"],
        "headers": [f"Part {i}"],
        "body": "x" * body_len,
        "url": "https://example.com/doc.pdf",
        "terms_used": None,
    }
    chunk.update(overrides)
    return chunk


def make_definition(term: str, definition: str = "means something;") -> dict:
    return {"document": "Doc", "term": term, "definition": definition}


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


class Workspace:
    """A throwaway chunks, definitions and golden directory for one document."""

    key = "doc"

    def __init__(self, root: Path):
        self.chunks_dir = root / "chunks"
        self.definitions_dir = root / "definitions"
        self.golden_dir = root / "golden"

    def write(self, chunks: list[dict], definitions: list[dict]) -> None:
        write_jsonl(self.chunks_dir / f"{self.key}.jsonl", chunks)
        write_jsonl(self.definitions_dir / f"{self.key}.jsonl", definitions)

    def save(self) -> None:
        save_golden(self.key, self.golden_dir, self.chunks_dir, self.definitions_dir)

    def compare(self) -> list[str]:
        return compare(self.key, self.golden_dir, self.chunks_dir, self.definitions_dir)

    def build(self) -> dict:
        return build_golden(self.key, self.chunks_dir, self.definitions_dir)


@pytest.fixture
def ws(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path)


def test_stats_are_calculated_from_body_and_definition_text(ws):
    ws.write(
        [make_chunk(1, 10), make_chunk(2, 20), make_chunk(3, 60)],
        [make_definition("a", "x" * 5), make_definition("b", "x" * 16)],
    )
    golden = ws.build()
    assert golden["chunks"]["stats"] == {
        "count": 3,
        "chars_total": 90,
        "chars_max": 60,
        "chars_min": 10,
        "chars_avg": 30.0,
    }
    assert golden["defs"]["stats"] == {
        "count": 2,
        "chars_total": 21,
        "chars_max": 16,
        "chars_min": 5,
        "chars_avg": 10.5,
    }


def test_document_with_no_definitions_gives_zeros(ws):
    ws.write([make_chunk(1)], [])
    assert ws.build()["defs"]["stats"] == {
        "count": 0,
        "chars_total": 0,
        "chars_max": 0,
        "chars_min": 0,
        "chars_avg": 0.0,
    }
    ws.save()
    assert ws.compare() == []


def test_unchanged_data_matches_its_golden(ws):
    ws.write([make_chunk(i) for i in range(5)], [make_definition("a")])
    ws.save()
    assert ws.compare() == []


def test_missing_golden_is_reported(ws):
    ws.write([make_chunk(1)], [])
    problems = ws.compare()
    assert len(problems) == 1
    assert "no golden stats" in problems[0]


def test_missing_processed_file_is_reported(ws):
    ws.write([make_chunk(1)], [])
    ws.save()
    (ws.chunks_dir / f"{ws.key}.jsonl").unlink()
    assert "processed file missing" in ws.compare()[0]


def test_a_removed_chunk_is_named_and_later_chunks_are_not(ws):
    chunks = [make_chunk(i) for i in range(6)]
    ws.write(chunks, [])
    ws.save()
    ws.write(chunks[:2] + chunks[3:], [])
    problems = "\n".join(ws.compare())
    assert "chunks.count: golden [6] | now [5]" in problems
    assert "chunks: no longer present [1]" in problems
    assert chunks[2]["chunk_id"] in problems
    # one insertion or deletion must not make every later chunk look wrong
    assert chunks[3]["chunk_id"] not in problems
    assert chunks[5]["chunk_id"] not in problems


def test_an_added_chunk_is_named(ws):
    chunks = [make_chunk(i) for i in range(3)]
    ws.write(chunks, [])
    ws.save()
    extra = make_chunk(9)
    ws.write(chunks + [extra], [])
    problems = "\n".join(ws.compare())
    assert "chunks: newly present [1]" in problems
    assert extra["chunk_id"] in problems


def test_a_changed_url_is_reported_even_though_the_chunk_id_is_unchanged(ws):
    chunks = [make_chunk(i) for i in range(3)]
    ws.write(chunks, [])
    ws.save()
    chunks[1] = make_chunk(1, url="https://example.com/other.pdf")
    ws.write(chunks, [])
    problems = "\n".join(ws.compare())
    assert "body, url, sectors, hierarchy or terms_used changed" in problems
    assert chunks[1]["chunk_id"] in problems
    assert "no longer present" not in problems


@pytest.mark.parametrize(
    "overrides",
    [
        {"sectors": ["class_1"]},
        {"hierarchy": "guidance"},
        {"terms_used": ["customer"]},
    ],
)
def test_other_metadata_changes_are_reported(ws, overrides):
    ws.write([make_chunk(1), make_chunk(2)], [])
    ws.save()
    ws.write([make_chunk(1), make_chunk(2, **overrides)], [])
    problems = "\n".join(ws.compare())
    assert "body, url, sectors, hierarchy or terms_used changed" in problems


def test_an_edited_body_with_the_same_chunk_id_names_the_chunk(ws):
    chunks = [make_chunk(i) for i in range(3)]
    ws.write(chunks, [])
    ws.save()
    chunks[1] = make_chunk(1, body_len=100, body="y" * 100)
    ws.write(chunks, [])
    problems = "\n".join(ws.compare())
    assert "body, url, sectors, hierarchy or terms_used changed" in problems
    assert chunks[1]["chunk_id"] in problems
    # same length, so the stats alone would not have noticed
    assert "chars_total" not in problems


def test_a_body_length_change_shows_in_the_stats_with_a_percentage(ws):
    ws.write([make_chunk(1, 100), make_chunk(2, 100)], [])
    ws.save()
    ws.write([make_chunk(1, 100), make_chunk(2, 50)], [])
    problems = "\n".join(ws.compare())
    assert "chunks.chars_total: golden [200] | now [150] (-25.0%)" in problems
    assert "chunks.chars_min: golden [100] | now [50] (-50.0%)" in problems


def test_reordered_chunks_report_the_first_position_that_differs(ws):
    chunks = [make_chunk(i) for i in range(4)]
    ws.write(chunks, [])
    ws.save()
    ws.write([chunks[0], chunks[2], chunks[1], chunks[3]], [])
    problems = "\n".join(ws.compare())
    assert "order differs, first difference at position [1]" in problems
    # same records, so nothing is reported missing and the stats agree
    assert "no longer present" not in problems
    assert "golden [" not in problems


def test_changed_definition_text_is_reported_by_term(ws):
    ws.write([make_chunk(1)], [make_definition("customer", "old wording;")])
    ws.save()
    ws.write([make_chunk(1)], [make_definition("customer", "new wording;")])
    problems = "\n".join(ws.compare())
    assert "same term but the definition text changed" in problems
    assert "customer" in problems


def test_duplicate_definition_terms_are_counted_not_collapsed(ws):
    definitions = [
        make_definition("record", "first meaning;"),
        make_definition("record", "second meaning;"),
    ]
    ws.write([make_chunk(1)], definitions)
    ws.save()
    assert ws.compare() == []
    ws.write([make_chunk(1)], definitions[:1])
    problems = "\n".join(ws.compare())
    assert "defs.count: golden [2] | now [1]" in problems
    assert "defs: no longer present [1]" in problems


@pytest.mark.parametrize("doc_key", TOOLBELT_REGISTRY.keys())
def test_committed_jsonl_matches_its_golden(doc_key: str):
    problems = compare(doc_key)
    if problems:
        pytest.fail(
            f"[{doc_key}] differs from data/processed/golden/{doc_key}.json:\n"
            + "\n".join(problems)
            + f"\nIf the change is intended: mrr pd --save-stats --doc {doc_key}",
            pytrace=False,
        )
