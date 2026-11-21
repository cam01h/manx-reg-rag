# Testing and CI

## Which tests run where

| Command | What runs | Needs |
| --- | --- | --- |
| `uv run pytest` | everything except the `live`, `qdrant` and `browser` tests (set in `pyproject.toml`) | nothing: no API key, no Qdrant, no model downloads |
| `uv run pytest -m qdrant` | checks the running Qdrant against the chunk jsonl | Qdrant running with the collection embedded |
| `uv run pytest -m browser` | the `web/` front end in a real headless Chromium, against canned server replies | `uv run playwright install chromium` once |
| `uv run pytest -m live` | checks every source url still works and the pdf behind it has not changed | internet, and the golden pdf hashes (see below) |

`-m` on the command line replaces the `not live and not qdrant and not browser` in `addopts`, so `-m live` runs only the live tests.

The `mrr pd --test-stats` flag runs just the golden stats tests (see `running_the_cli.md`).

## What the processed-data tests catch

- `tests/extraction_ops/test_jsonl_stats.py` notices that the jsonl **changed** since the golden stats in `data/processed/golden/` were saved.
- `tests/extraction_ops/test_jsonl_invariants.py` notices that the jsonl is **invalid**, whether or not it changed: an unknown sector name, an empty sector list, a url that is not https, a blank body, a duplicate `chunk_id`, a missing definitions file, or a jsonl file with no toolbelt. A failure names the document and lists the first few offending chunks.

When you add a document or a new version of one, expect the stats test to ask for `mrr pd --save-stats --doc <key>` and the invariants test to tell you if the new data breaks a rule.

## Browser tests (`tests/browser`)

These load the real `web/index.html` and `web/app.js` in a headless Chromium and use the page the way a person does: type a question, tick sectors, click Reset, resize to a phone. The server is not started. `tests/browser/fake_api.py` answers the four requests the page makes (`/query`, `/reset`, `/sectors`, `/documents`) with canned replies and records what the page sent, and anything else the page tries to load is blocked. So they need no API key, Qdrant or models, and the whole set takes under a minute.

```bash
uv run playwright install chromium     # once per machine, about 150 MB
uv run pytest -m browser               # headless
uv run pytest -m browser --headed -k reset --slowmo 500   # watch one test
```

What they cover: the streamed progress lines and answer, markdown rendering, the request body (prompt, session id, ticked sectors), citation links (https only, new tab, `noopener noreferrer`), tidied citation titles, error and half-finished replies, the busy state and the double-send guard, Reset, the citations toggle, remembered sectors, and horizontal overflow on a phone-sized screen.

Things to know:

- **Hooks.** Elements are found by the ids in `index.html` or by `data-testid` attributes (`user-turn`, `assistant-turn`, `citation`, `progress`, `error`) that `app.js` now sets, not by styling classes, so a restyle does not break the tests. If you rebuild the page (htmx, say), keep those attributes and the tests still apply.
- **`marked` is vendored.** The page loads the markdown library from a CDN. The tests serve `tests/browser/vendor/marked.umd.js` (MIT, version in its header) instead, so results do not depend on what the CDN serves. The CDN link in `index.html` is not pinned to a version; the tests cannot see a change in what it serves.
- **Known gap, marked `xfail`.** `test_html_in_an_answer_does_not_run` shows that HTML in an answer runs, because `app.js` sets `innerHTML` from `marked.parse(...)` without sanitising it. The test is `xfail(strict=True)`: it reports as expected-failure now, and fails loudly once the page is fixed so that the marker gets removed.
- **After editing `app.js`**, bump the `?v=` on its script tag in `index.html` as usual; the tests do not care.

## CI (GitHub Actions)

The workflows are in `.github/workflows/`.

**`ci.yml`** has two jobs that run side by side on fresh Linux machines. `checks` runs `ruff check`, `ruff format --check` and the default `pytest`. `browser` installs Chromium and runs `pytest -m browser`; when it fails, the run page keeps screenshots and Playwright traces of the failures for 14 days (download the `browser-test-results` artifact, and open a trace at <https://trace.playwright.dev> to replay what the page did). It runs:

- on every pull request (each push to the PR's branch runs it again)
- on every push to `main`, which also covers a local merge pushed straight to `main`
- on demand: Actions tab, CI, Run workflow, pick a branch

Pushes to other branches run nothing, so half-finished work can be pushed freely. To get a branch checked early, open it as a draft pull request. Adding `[skip ci]` to a commit message skips the run for that commit.

The result is a green tick or red cross on the commit and on the pull request. Click it, then the failed step, for the same output you get locally. A failed run emails you. It does not stop a push, and it only stops a merge if you turn on branch protection and require the `checks` and `browser` jobs (Settings, Rules or Branches; the check only appears in that list after it has run once).

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
