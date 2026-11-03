"""Golden statistics for the processed chunk and definition files.

`mrr pd --save-stats` writes one json file per document to GOLDEN_DIR describing
the jsonl that `mrr pd --ingest` produced. `mrr pd --stats` and the pytest
recompute the same description from the jsonl and compare it with the saved one.

Each golden file holds, for chunks and for definitions:
  stats    count and character totals (chunks: len(body), definitions: len(definition))
  entries  one string per record, in file order: "<identity>  #<short hash>"
             chunks:      identity is chunk_id (which already contains a hash of the
                          body); the hash covers body, url, sectors, hierarchy, terms_used
             definitions: identity is the term; the hash covers the definition text

compare() returns a list of problems and never exits, so the CLI and pytest can
both use it.
"""

import hashlib
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

from config import CHUNKS_DIR, DEFINITIONS_DIR, GOLDEN_DIR

logger = logging.getLogger(__name__)

SEPARATOR = "  #"
HASH_LENGTH = 8
SHOW_LIMIT = 5
SECTIONS = ("chunks", "defs")
CHANGED_LABELS = {
    "chunks": "same chunk_id but body, url, sectors, hierarchy or terms_used changed",
    "defs": "same term but the definition text changed",
}


def _short_hash(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(text.encode()).hexdigest()[:HASH_LENGTH]


def _entry(identity: str, fingerprint: Any) -> str:
    return f"{identity}{SEPARATOR}{_short_hash(fingerprint)}"


def _identity(entry: str) -> str:
    return entry.rpartition(SEPARATOR)[0]


def chunk_entry(chunk: dict) -> str:
    fingerprint = [
        chunk["body"],
        chunk["url"],
        chunk["sectors"],
        chunk["hierarchy"],
        chunk.get("terms_used"),
    ]
    return _entry(chunk["chunk_id"], fingerprint)


def definition_entry(definition: dict) -> str:
    return _entry(definition["term"], definition["definition"])


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _stats(lengths: list[int]) -> dict[str, int | float]:
    # a document with no definitions has an empty file, so every figure is zero
    if not lengths:
        return {
            "count": 0,
            "chars_total": 0,
            "chars_max": 0,
            "chars_min": 0,
            "chars_avg": 0.0,
        }
    total = sum(lengths)
    return {
        "count": len(lengths),
        "chars_total": total,
        "chars_max": max(lengths),
        "chars_min": min(lengths),
        "chars_avg": round(total / len(lengths), 1),
    }


def build_golden(
    key: str,
    chunks_dir: Path = CHUNKS_DIR,
    definitions_dir: Path = DEFINITIONS_DIR,
) -> dict:
    chunks = _read_jsonl(chunks_dir / f"{key}.jsonl")
    definitions = _read_jsonl(definitions_dir / f"{key}.jsonl")
    return {
        "chunks": {
            "stats": _stats([len(c["body"]) for c in chunks]),
            "entries": [chunk_entry(c) for c in chunks],
        },
        "defs": {
            "stats": _stats([len(d["definition"]) for d in definitions]),
            "entries": [definition_entry(d) for d in definitions],
        },
    }


def save_golden(
    key: str,
    golden_dir: Path = GOLDEN_DIR,
    chunks_dir: Path = CHUNKS_DIR,
    definitions_dir: Path = DEFINITIONS_DIR,
) -> Path:
    golden = build_golden(key, chunks_dir, definitions_dir)
    path = golden_dir / f"{key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    # indent puts every entry on its own line, so a git diff shows exactly which changed
    path.write_text(
        json.dumps(golden, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path


def _percent_change(old: Any, new: Any) -> str:
    if (
        not isinstance(old, (int, float))
        or not isinstance(new, (int, float))
        or not old
    ):
        return "n/a"
    return f"{(new - old) / old * 100:+.1f}%"


def _compare_stats(section: str, golden: dict, current: dict) -> list[str]:
    problems = []
    for field, found in current.items():
        expected = golden.get(field)
        if found != expected:
            problems.append(
                f"{section}.{field}: golden [{expected}] | now [{found}] "
                f"({_percent_change(expected, found)})"
            )
    return problems


def _list_ids(heading: str, ids: Counter) -> list[str]:
    shown = list(ids.elements())
    lines = [f"{heading} [{len(shown)}], first {min(SHOW_LIMIT, len(shown))}:"]
    lines += [f"    {identity}" for identity in shown[:SHOW_LIMIT]]
    return lines


def _compare_entries(section: str, golden: list[str], current: list[str]) -> list[str]:
    if golden == current:
        return []
    removed = Counter(golden) - Counter(current)
    added = Counter(current) - Counter(golden)
    removed_ids = Counter(_identity(e) for e in removed.elements())
    added_ids = Counter(_identity(e) for e in added.elements())
    # an id on both sides means the record is still there but its fingerprint moved
    gone = removed_ids - added_ids
    new = added_ids - removed_ids
    changed = removed_ids & added_ids

    problems = []
    if gone:
        problems += _list_ids(f"{section}: no longer present", gone)
    if new:
        problems += _list_ids(f"{section}: newly present", new)
    if changed:
        problems += _list_ids(f"{section}: {CHANGED_LABELS[section]}", changed)
    if not problems:
        # same records, different order: report the first position that differs
        for i, (g, c) in enumerate(zip(golden, current)):
            if g != c:
                problems.append(
                    f"{section}: order differs, first difference at position [{i}]"
                )
                problems.append(f"    golden: {g}")
                problems.append(f"    now:    {c}")
                break
    return problems


def compare(
    key: str,
    golden_dir: Path = GOLDEN_DIR,
    chunks_dir: Path = CHUNKS_DIR,
    definitions_dir: Path = DEFINITIONS_DIR,
) -> list[str]:
    path = golden_dir / f"{key}.json"
    if not path.exists():
        return [f"no golden stats for [{key}] at [{path}]"]
    try:
        current = build_golden(key, chunks_dir, definitions_dir)
    except FileNotFoundError as e:
        return [f"processed file missing for [{key}]: [{e.filename}]"]
    golden = json.loads(path.read_text(encoding="utf-8"))

    problems = []
    for section in SECTIONS:
        golden_section = golden.get(section, {})
        problems += _compare_stats(
            section, golden_section.get("stats", {}), current[section]["stats"]
        )
        problems += _compare_entries(
            section, golden_section.get("entries", []), current[section]["entries"]
        )
    return problems
