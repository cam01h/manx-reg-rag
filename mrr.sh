#!/usr/bin/env bash
set -euo pipefail

# always run from the repo root, wherever this is called from
cd "$(dirname "${BASH_SOURCE[0]}")"

# "host" runs python with uv on this machine (laptop)
# "container" runs it inside the app image (server, the default)
MRR_PYTHON="${MRR_PYTHON:-container}"

run_python() {
  if [ "$MRR_PYTHON" = "host" ]; then
    uv run python "$@"
  else
    docker compose run --rm --no-deps app uv run python "$@"
  fi
}

usage() {
  cat <<EOF
usage: mrr <command> [args]

stack
  up            start the stack (default)
  down          stop the stack
  ps            list containers
  rebuild       rebuild the app image and restart
  deploy        git pull, then rebuild
  shell         open a shell in the app container

pipeline
  pd [args]     process documents      e.g. mrr pd --ingest --doc handbook
  embed [args]  embed chunks to qdrant e.g. mrr embed --rebuild
  diag [args]   diagnostics cli        e.g. mrr diag norm_sections handbook -ft
EOF
}

cmd="${1:-up}"
[[ $# -gt 0 ]] && shift

case "$cmd" in
up)
  docker compose up -d
  echo "stack running"
  ;;
down)
  docker compose down
  ;;
ps)
  docker compose ps
  ;;
rebuild)
  docker compose up -d --build
  ;;
deploy)
  git pull
  docker compose up -d --build
  ;;
shell)
  docker compose run --rm --no-deps app bash
  ;;
pd)
  run_python -m extraction_ops.process_documents "$@"
  ;;
embed)
  docker compose up -d qdrant
  echo "embedding (${MRR_PYTHON})..."
  run_python -m db_ops.embed "$@"
  # recreate so the app reloads its cached definitions
  docker compose up -d --force-recreate app
  echo "stack running"
  ;;
diag)
  run_python -m tests.extraction_ops.diagnostics.cli "$@"
  ;;
qm)
  docker compose up -d qdrant
  [[ $# -eq 0 ]] && set -- --dense --sparse --hybrid
  for mode in "$@"; do
    mode="${mode#--}"
    echo "query metrics [${mode}] (${MRR_PYTHON})..."
    run_python -m tests.db_ops.query_metrics.query_test --mode "$mode"
  done
  ;;
help | -h | --help)
  usage
  ;;
*)
  usage
  exit 1
  ;;
esac
