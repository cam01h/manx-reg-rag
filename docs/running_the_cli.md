# Running the CLI

## Using a command line interface (CLI)

Well done to any compliance officer will to tangle with a unix shell, I salute you. If you are an IT person who has been passed this to set up, thank you for helping your compliance team. Either way i have tried to keep the documentation clear.

Everything runs through one command, `mrr`, which wraps `mrr.sh` in the repo root.
Server tools (memory, logs, tmux) live as separate shortcuts in `server-aliases.sh`.

Run `mrr help` at any time for the short version of this page.

---

## Setup

For the time being, this is a linux only application. Adapting the existing code to handle both windows and linux machines is on the roadmap though.

The code is however designed to handle both a dev machine and a laptop in the corner situation. When you are running this on an old laptop, dev tools like uv and python may not be installed so the code can be run through the app container running your application.

Add these to `~/.bashrc` on each machine. `.bashrc` is not in the repo, so each machine keeps its own values.

**My machine had python and uv installed**

```bash
export MRR=/home/<you>/workspaces/manx-reg-rag
export MRR_PYTHON=host
source "$MRR/server-aliases.sh"
```

**I am repurposing and old laptop**

```bash
export MRR=/opt/manx-reg-rag
source "$MRR/server-aliases.sh"
```

Open a terminal and run `source ~/.bashrc`. This will update what you just added to the terminal you are working in.

| Variable     | What it does |
|--------------|--------------|
| `MRR`        | Path to the repo. Every command uses it, so they work from any folder. |
| `MRR_PYTHON` | Where Python commands run. `host` uses `uv` on this machine; anything else (or unset) runs inside the app container. |

To override `MRR_PYTHON` for a single run, put it in front of the command, e.g. `MRR_PYTHON=container mrr pd --ingest`.

You have to set this variable in your .bashrc file or none of the follow will work!

## I don't want to read this whole document, i just want to get started on a spare laptop

Fair enough:
  1. open a terminal
  2. run the following commands:
    - "mrr up"
    - "mrr deploy"
    - "mrr embed" - this will take a while I'm afraid (possibly up to 20 minutes) but be patient
  3. open a browser and go to "http://localhost:8000/" and your in!

http://localhost:8000/ will work for any computer on the same local network but the code will run on your machine so handling multiple users will be slow.

---

## `mrr` commands

`mrr <command> [args]`. With no command, `mrr` runs `up`.

### Stack
[Running the application]

| Command       | What it does |
|---------------|--------------|
| `mrr up`      | Start the stack (Qdrant, app, Cloudflare tunnel) in the background. |
| `mrr down`    | Stop the stack. Data in the Qdrant volume is kept. |
| `mrr ps`      | List the containers and their status. |
| `mrr rebuild` | Rebuild the app image and restart it. Use after code changes. |
| `mrr deploy`  | `git pull`, then rebuild. The usual way to update the server. |
| `mrr shell`   | Open a bash shell inside a fresh app container. |

### Pipeline
[Filling the db with chunks]

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

**Output:** `data/processed/chunks/<key>.jsonl` and `data/processed/definitions/<key>.jsonl`. Running with `--doc` only rewrites that document's two files. A document with no definitions gets an empty definitions file, so stale definitions can never survive.

**Watch out:**

- `--get-pdfs` (and the no-flag run) fails for legislation.gov.im documents: the site blocks automated downloads. Download those by hand into the path set in the toolbelt's `pdf_path`. The PDFs are committed to the repo, so this is only needed when a document changes.
- PDF handlers modify the PDF **in place**. Only run `--handle-pdfs` on a freshly downloaded PDF. Running it a second time applies the handlers again — for the Handbook, that removes another page.

**Examples**

```bash
mrr pd --ingest                       # re-ingest everything
mrr pd --ingest --doc poca            # re-ingest just the POCA
mrr pd --handle-pdfs --doc handbook   # apply handlers to a freshly downloaded handbook PDF
```

---

## `mrr embed` — embed chunks into Qdrant

Reads every file in `data/processed/chunks/` and syncs the Qdrant collection with them.

```bash
mrr embed [--rebuild]
```

| Flag        | What it does |
|-------------|--------------|
| *(none)*    | Incremental: embeds only new chunks and deletes chunks that no longer exist. Unchanged chunks are left alone, so a run with no changes is quick. |
| `--rebuild` | Deletes the collection and embeds everything from scratch. Use this when you change the embedding model. |

It starts Qdrant first if needed, and recreates the app container at the end so the app reloads its cached definitions.

---

## `mrr diag` — diagnostics

Firms should feel at liberty to add their own documents. Greater guidance will be added on this in future but for now these are the tools used to add th public documents.

Runs a single pipeline stage for a single document, so you can inspect its output or check it against a known-good "golden" file. Use it when adding a document or changing a toolbelt.

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
| `headers`       | Just the header path of each section, one per line — quick to scan. |
| `norm_sections` | Sections after cleaning, splitting and merging — what becomes chunks. |
| `def_segs`      | Definition text split into one segment per term (from `def_lines`). |
| `definitions`   | Parsed definitions. |
| `variants`      | Plural/singular variants for each defined term. |

**Output:** `tests/extraction_ops/diagnostics/data/<stage>/<doc>_<mode>.<ext>`. Stages that produce objects also write a `.json` alongside the readable `.md`.

**Notes**

- The PDF stages and `raw_md` can't chain, so use `-f` for those.
- `-t` stops at the first difference and shows the expected and found lines.
- `diag` is a laptop tool. On the server the container has neither the test data folder nor the dev dependencies.

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

| Command                  | What it does |
|--------------------------|--------------|
| `cdm`                    | `cd` to the repo. |
| `deploy`                 | `mrr deploy`, then reload these aliases so any new ones are available. |
| `log-l [lines] [service]`| Follow live logs, starting from the last `lines` (default 20). e.g. `log-l 100 app` |
| `logs-g <term> [lines]`  | Search all logs for `term` and show the last `lines` matches (default 20). e.g. `logs-g ERROR 50` |
| `mem`                    | Memory use of the app's uvicorn process. |
| `main`, `dev`            | Reattach to the `main` or `dev` tmux session. |

Press `Ctrl-c` to stop following logs. The containers keep running.

---

## Common workflows

**Update or add a document (laptop)**

```bash
mrr pd --handle-pdfs --doc handbook   # only for a freshly downloaded PDF
mrr diag norm_sections handbook -c -t # check nothing unexpected changed
mrr pd --ingest --doc handbook
mrr embed
```

**Ship code to the server**

```bash
deploy
```
