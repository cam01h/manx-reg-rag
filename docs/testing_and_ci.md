# Testing and CI

## Which tests run where

| Command | What runs | Needs |
| --- | --- | --- |
| `uv run pytest` | everything except the `live` and `qdrant` tests (set in `pyproject.toml`) | nothing: no API key, no Qdrant, no model downloads |
| `uv run pytest -m qdrant` | checks the running Qdrant against the chunk jsonl | Qdrant running with the collection embedded |
| `uv run pytest -m live` | checks every source url still works and the pdf behind it has not changed | internet, and the golden pdf hashes (see below) |

`-m` on the command line replaces the `not live and not qdrant` in `addopts`, so `-m live` runs only the live tests.

The `mrr pd --test-stats` flag runs just the golden stats tests (see `running_the_cli.md`).

## What the processed-data tests catch

- `tests/extraction_ops/test_jsonl_stats.py` notices that the jsonl **changed** since the golden stats in `data/processed/golden/` were saved.
- `tests/extraction_ops/test_jsonl_invariants.py` notices that the jsonl is **invalid**, whether or not it changed: an unknown sector name, an empty sector list, a url that is not https, a blank body, a duplicate `chunk_id`, a missing definitions file, or a jsonl file with no toolbelt. A failure names the document and lists the first few offending chunks.

When you add a document or a new version of one, expect the stats test to ask for `mrr pd --save-stats --doc <key>` and the invariants test to tell you if the new data breaks a rule.

## CI (GitHub Actions)

The workflows are in `.github/workflows/`.

**`ci.yml`** runs `ruff check`, `ruff format --check` and the default `pytest` on a fresh Linux machine. It runs:

- on every pull request (each push to the PR's branch runs it again)
- on every push to `main`, which also covers a local merge pushed straight to `main`
- on demand: Actions tab, CI, Run workflow, pick a branch

Pushes to other branches run nothing, so half-finished work can be pushed freely. To get a branch checked early, open it as a draft pull request. Adding `[skip ci]` to a commit message skips the run for that commit.

The result is a green tick or red cross on the commit and on the pull request. Click it, then the failed step, for the same output you get locally. A failed run emails you. It does not stop a push, and it only stops a merge if you turn on branch protection and require the `checks` job (Settings, Rules or Branches; the check only appears in that list after it has run once).

**`live.yml`** runs the `live` tests every Monday at 06:17 UTC and on demand. A red result means a source url has died or a source pdf has changed upstream. It needs two things:

1. The golden pdf hashes, committed. `tests/extraction_ops/diagnostics/data/` is ignored by git except for the `*_golden_hash.txt` files in `raw_pdf/`, so after saving goldens with the diagnostics CLI:

   ```bash
   git add tests/extraction_ops/diagnostics/data/raw_pdf/*_golden_hash.txt
   ```

   Without them every document fails with "No golden hash found".
2. To be on the default branch. GitHub only runs scheduled workflows from there, and it pauses them after 60 days without any activity in the repository (the Actions tab offers a button to turn them back on).

If a source website refuses GitHub's servers, the live run will fail on those urls even though they work from your machine. The first manual run tells you.

## Changing a pinned dependency or the Python version

CI installs exactly what `uv.lock` says (`uv sync --frozen`) and the Python version in `.python-version`, so updating either is the same change locally and in CI.
