# Running the CLI

## Using a command line interface (CLI)

Well done to any compliance officer willing to tangle with a Unix shell, I salute you. If you're an IT person who has been passed this to set up, thank you for helping your compliance team. Either way, I've tried to keep this as clear as I can.

If you haven't set the tool up yet, start with the [getting started guide](getting_started.md) and come back here once it's running. This page is the reference for every command once you're up and going.

Everything runs through one command, `mrr`, which wraps `mrr.sh` in the repo root. Server tools (memory, logs, tmux) live as separate shortcuts in `server-aliases.sh`.

Forgotten something? Run `mrr help` at any time for the short version of this page.

---

## Setup

For the time being, this is a Linux-only application. Adapting it to run on Windows as well is on the roadmap.

The code is designed to work on both a dev machine and a laptop-in-the-corner. An old laptop may not have dev tools like Python and uv installed, so instead the commands run inside the app's own container, which already has everything it needs.

Add these lines to `~/.bashrc` on each machine, changing the path to wherever you cloned the repo. `.bashrc` isn't part of the repo, so each machine keeps its own settings and a `git pull` will never overwrite them.

**My machine has Python and uv installed**

```bash
export MRR=/home/<you>/workspaces/manx-reg-rag
export MRR_PYTHON=host
source "$MRR/server-aliases.sh"
```

**I'm repurposing an old laptop**

```bash
export MRR=/opt/manx-reg-rag
source "$MRR/server-aliases.sh"
```

Then run `source ~/.bashrc`. This loads what you've just added into the terminal you're working in. New terminals pick it up automatically.

| Variable     | Required? | What it does |
|--------------|-----------|--------------|
| `MRR`        | Yes       | Path to the repo. Every command uses it, so they work from any folder. Without it, none of the commands below will work! |
| `MRR_PYTHON` | No        | Where Python commands run. `host` uses uv on this machine. Leave it unset and they run inside the app container. |

To override `MRR_PYTHON` for a single run, put it in front of the command, e.g. `MRR_PYTHON=container mrr pd --ingest`.

---

## `mrr` commands

`mrr <command> [args]`. With no command, `mrr` runs `up`.

### Stack

*Running the application.*

| Command       | What it does |
|---------------|--------------|
| `mrr up`      | Start the stack (Qdrant, the app and the Cloudflare tunnel) in the background. |
| `mrr down`    | Stop the stack. Data in the Qdrant volume is kept. |
| `mrr ps`      | List the containers and their status. |
| `mrr rebuild` | Rebuild the app image and restart it. Use after code changes. |
| `mrr deploy`  | `git pull`, then rebuild. The usual way to update. |
| `mrr shell`   | Open a bash shell inside a fresh app container. |

The Cloudflare tunnel is only needed if you're publishing the app online. Without a tunnel token its container will keep restarting. That's harmless and the app still works locally, so you can safely ignore it.

### Pipeline

*Filling the database with chunks.*

| Command            | What it does |
|--------------------|--------------|
| `mrr pd [args]`    | Process documents: PDFs → chunks and definitions. |
| `mrr embed [args]` | Embed chunks into Qdrant. |
| `mrr diag [args]`  | Diagnostics: run and test one pipeline stage at a time. |

---

## `mrr pd` — process documents

Turns PDFs into chunk and definition files, one pair per document.

```bash
mrr pd [--doc KEY] [--get-pdfs | --handle-pdfs | --ingest]
```

| Flag            | What it does |
|-----------------|--------------|
| `--doc KEY`     | Only process one document. Leave it out to process all of them. |
| `--get-pdfs`    | Download PDFs from each toolbelt's URL. |
| `--handle-pdfs` | Apply each toolbelt's PDF handlers (page removal, redactions). |
| `--ingest`      | Extract chunks and definitions and write them to `data/processed/`. |
| *(no flag)*     | All three in order: get, handle, ingest. |

**Document keys:** `code`, `handbook`, `supplemental`, `poca`, `fiu`, `tcivpen`, `antiterror`, `rao`, `terrorfr`, `dbroa`, `sanctions`.

**Output:** `data/processed/chunks/<key>.jsonl` and `data/processed/definitions/<key>.jsonl`. Running with `--doc` only rewrites that document's two files. A document with no definitions gets an empty definitions file, so stale definitions can never hang around.

**Watch out:**

- `--get-pdfs` (and the no-flag run) fails for legislation.gov.im documents, because the site blocks automated downloads. Download those by hand into the path set in the toolbelt's `pdf_path`. The PDFs are already in the repo, so you only need to do this when a document changes.
- PDF handlers modify the PDF **in place**. Only run `--handle-pdfs` on a freshly downloaded PDF. Running it a second time applies the handlers again, and for the Handbook that removes another page.

**Examples**

```bash
mrr pd --ingest                       # re-ingest everything
mrr pd --ingest --doc poca            # re-ingest just POCA
mrr pd --handle-pdfs --doc handbook   # apply handlers to a freshly downloaded Handbook PDF
```

---

## `mrr embed` — embed chunks into Qdrant

Reads every file in `data/processed/chunks/` and brings the Qdrant database in line with them.

```bash
mrr embed [--rebuild]
```

| Flag        | What it does |
|-------------|--------------|
| *(none)*    | Incremental: embeds only new chunks and deletes chunks that no longer exist. Unchanged chunks are left alone, so a run with no changes is quick. |
| `--rebuild` | Deletes the database and embeds everything from scratch. Use this when you change the embedding model. |

It starts Qdrant first if needed, and restarts the app at the end so it picks up any new definitions.

The first full embed takes a while (possibly up to 20 minutes on a modest machine). Put the kettle on.

---

## `mrr diag` — diagnostics

Firms should feel at liberty to add their own documents. Fuller guidance on that is coming, but for now these are the tools I used to add the public documents.

`diag` runs a single pipeline stage for a single document, so you can inspect its output or check it against a known-good "golden" file. Use it when adding a document or changing a toolbelt.

```bash
mrr diag <stage> <doc> (-c | -f) (-r | -g | -t)
```

You must give one **source** flag and one **mode** flag.

| Source | Meaning |
|--------|---------|
| `-c`   | Chain: run every stage from the `raw_md` golden file up to this one. |
| `-f`   | From golden: use the previous stage's golden file as input. |

| Mode | Meaning |
|------|---------|
| `-r` | Write a test file for inspection. |
| `-g` | Write (or overwrite) the golden file. |
| `-t` | Run the stage and compare the result against the existing golden file. |

**Stages, in pipeline order**

| Stage           | Produces |
|-----------------|----------|
| `raw_pdf`       | The downloaded PDF. |
| `handled_pdf`   | The PDF after the toolbelt's handlers. |
| `raw_md`        | Markdown extracted from the handled PDF. |
| `clean`         | Markdown after the toolbelt's text cleaner. |
| `trimmed`       | Clean markdown trimmed to the document's start and end markers. |
| `chunk_lines`   | Lines that feed chunking. |
| `def_lines`     | Lines that feed definition extraction. |
| `raw_sections`  | Sections split by headers (from `chunk_lines`). |
| `headers`       | Just the header path of each section, one per line. Quick to scan. |
| `norm_sections` | Sections after cleaning, splitting and merging. This is what becomes chunks. |
| `def_segs`      | Definition text split into one segment per term (from `def_lines`). |
| `definitions`   | Parsed definitions. |
| `variants`      | Plural and singular variants for each defined term. |

**Output:** `tests/extraction_ops/diagnostics/data/<stage>/<doc>_<mode>.<ext>`. Stages that produce objects also write a `.json` file alongside the readable `.md`.

**Notes**

- The PDF stages and `raw_md` can't chain, so use `-f` for those.
- `-t` stops at the first difference and shows you the expected and found lines.
- `diag` needs a machine with Python and uv (`MRR_PYTHON=host`). The app container has neither the test data folder nor the dev tools.

**Examples**

```bash
mrr diag norm_sections handbook -c -t   # full chain, check against golden
mrr diag definitions code -f -r         # write a test file from the def_lines golden
mrr diag headers handbook -f -r         # scan the header structure
```

`diag` on its own is a shortcut for `mrr diag`.

---

## Server tools

Defined in `server-aliases.sh`.

| Command                   | What it does |
|---------------------------|--------------|
| `cdm`                     | Jump to the repo folder. |
| `deploy`                  | `mrr deploy`, then reload these shortcuts so any new ones are available. |
| `log-l [lines] [service]` | Follow live logs, starting from the last `lines` (default 20), e.g. `log-l 100 app`. |
| `logs-g <term> [lines]`   | Search all logs for `term` and show the last `lines` matches (default 20), e.g. `logs-g ERROR 50`. |
| `mem`                     | Memory use of the app's web server process. |
| `main`, `dev`             | Reattach to the `main` or `dev` tmux session. |

Press `Ctrl-c` to stop following logs. Don't worry, the app keeps running.

---

## Common workflows

**Update or add a document**

```bash
mrr pd --handle-pdfs --doc handbook   # only for a freshly downloaded PDF
mrr diag norm_sections handbook -c -t # check nothing unexpected changed
mrr pd --ingest --doc handbook
mrr embed
```

**Pick up the latest code**

```bash
deploy
```
