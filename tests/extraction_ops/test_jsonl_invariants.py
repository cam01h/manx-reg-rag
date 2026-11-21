"""Rules the processed jsonl must always follow, whatever the document says.

The golden stats (test_jsonl_stats.py) notice that something changed. These
tests notice that something is *invalid*, which matters most when a new
document or a new version of one is added: a typo in a sector name, a chunk
without a url or a missing definitions file would otherwise only show up as a
confusing retrieval result.

Each document is its own test, so a failure names the document and lists the
first few offending records.
"""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from config import CHUNKS_DIR, DEFINITIONS_DIR
from core.sectors import SECTOR_LABELS
from extraction_ops import TOOLBELT_REGISTRY

SHOW_LIMIT = 5
VALID_SECTORS = set(SECTOR_LABELS)
VALID_HIERARCHIES = {
    "primary legislation",
    "secondary legislation",
    "guidance",
    "national risk assessment",
    "supplemental",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def offenders(
    records: list[dict[str, Any]],
    is_bad: Callable[[dict[str, Any]], bool],
    name: Callable[[dict[str, Any]], str],
) -> list[str]:
    bad = [name(r) for r in records if is_bad(r)]
    if not bad:
        return []
    return [f"[{len(bad)}] records, first {min(SHOW_LIMIT, len(bad))}:"] + [
        f"    {b}" for b in bad[:SHOW_LIMIT]
    ]


def chunk_problems(key: str, chunks: list[dict[str, Any]]) -> list[str]:
    tools = TOOLBELT_REGISTRY[key]
    chunk_id = lambda c: c["chunk_id"]
    checks: list[tuple[str, Callable[[dict[str, Any]], bool]]] = [
        (
            f"document is not [{tools.document}] (the toolbelt's name)",
            lambda c: c["document"] != tools.document,
        ),
        (
            f"hierarchy is not [{tools.hierarchy}] (the toolbelt's hierarchy)",
            lambda c: c["hierarchy"] != tools.hierarchy,
        ),
        (
            "hierarchy is not one of the known values",
            lambda c: c["hierarchy"] not in VALID_HIERARCHIES,
        ),
        (
            "chunk_id does not start with the document name",
            lambda c: not c["chunk_id"].startswith(c["document"]),
        ),
        (
            "no sectors (the sector filter would never return it)",
            lambda c: not c["sectors"],
        ),
        (
            "unknown sector name (not in core/sectors.py SECTOR_LABELS)",
            lambda c: not set(c["sectors"]) <= VALID_SECTORS,
        ),
        (
            "the same sector is listed twice",
            lambda c: len(set(c["sectors"])) != len(c["sectors"]),
        ),
        (
            "url is not https",
            lambda c: not c["url"].startswith("https://"),
        ),
        (
            "every header is blank",
            lambda c: not any(h.strip() for h in c["headers"]),
        ),
        (
            "body is blank",
            lambda c: not c["body"].strip(),
        ),
    ]
    problems = []
    for message, is_bad in checks:
        found = offenders(chunks, is_bad, chunk_id)
        if found:
            problems += [f"{message}: {found[0]}"] + found[1:]

    seen: set[str] = set()
    duplicates = []
    for c in chunks:
        if c["chunk_id"] in seen:
            duplicates.append(c["chunk_id"])
        seen.add(c["chunk_id"])
    if duplicates:
        problems.append(
            f"duplicate chunk_id: [{len(duplicates)}] records, first "
            f"{min(SHOW_LIMIT, len(duplicates))}:"
        )
        problems += [f"    {d}" for d in duplicates[:SHOW_LIMIT]]
    return problems


def definition_problems(key: str, definitions: list[dict[str, Any]]) -> list[str]:
    tools = TOOLBELT_REGISTRY[key]
    term = lambda d: d["term"]
    checks: list[tuple[str, Callable[[dict[str, Any]], bool]]] = [
        (
            f"document is not [{tools.document}] (the toolbelt's name)",
            lambda d: d["document"] != tools.document,
        ),
        ("term is blank", lambda d: not d["term"].strip()),
        ("definition is blank", lambda d: not d["definition"].strip()),
    ]
    problems = []
    for message, is_bad in checks:
        found = offenders(definitions, is_bad, term)
        if found:
            problems += [f"{message}: {found[0]}"] + found[1:]
    return problems


@pytest.mark.parametrize("doc_key", TOOLBELT_REGISTRY.keys())
def test_processed_files_follow_the_rules(doc_key: str):
    chunks_path = CHUNKS_DIR / f"{doc_key}.jsonl"
    definitions_path = DEFINITIONS_DIR / f"{doc_key}.jsonl"
    problems = []
    for path in (chunks_path, definitions_path):
        if not path.exists():
            problems.append(f"missing file: [{path}]")
    if not problems:
        chunks = read_jsonl(chunks_path)
        if not chunks:
            problems.append(f"[{chunks_path}] has no chunks")
        problems += chunk_problems(doc_key, chunks)
        # a document may legitimately have no definitions, so only the records are checked
        problems += definition_problems(doc_key, read_jsonl(definitions_path))
    if problems:
        pytest.fail(
            f"[{doc_key}] processed files break a rule:\n" + "\n".join(problems),
            pytrace=False,
        )


def test_chunk_ids_are_unique_across_all_documents():
    # the chunk_id becomes the qdrant point id, so a clash would silently overwrite a point
    owners: dict[str, str] = {}
    clashes = []
    for key in TOOLBELT_REGISTRY:
        for chunk in read_jsonl(CHUNKS_DIR / f"{key}.jsonl"):
            first = owners.setdefault(chunk["chunk_id"], key)
            if first != key:
                clashes.append(f"{chunk['chunk_id']} (in {first} and {key})")
    if clashes:
        pytest.fail(
            f"chunk_id shared between documents [{len(clashes)}], first "
            f"{min(SHOW_LIMIT, len(clashes))}:\n"
            + "\n".join(f"    {c}" for c in clashes[:SHOW_LIMIT]),
            pytrace=False,
        )


def test_every_processed_file_belongs_to_a_registered_document():
    orphans = [
        f"{directory.name}/{path.name}"
        for directory in (CHUNKS_DIR, DEFINITIONS_DIR)
        for path in sorted(directory.glob("*.jsonl"))
        if path.stem not in TOOLBELT_REGISTRY
    ]
    if orphans:
        pytest.fail(
            "jsonl files with no toolbelt in TOOLBELT_REGISTRY (renamed or removed "
            "document?):\n" + "\n".join(f"    {o}" for o in orphans),
            pytrace=False,
        )
