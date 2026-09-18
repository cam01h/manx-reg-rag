#!/usr/bin/env bash
set -euo pipefail

MRR_PYTHON="${MRR_PYTHON:-container}"

run_python() {
  if [ "$MRR_PYTHON" = "host" ]; then
    uv run python "$@"
  else
    docker compose run --rm --no-deps app uv run python "$@"
  fi
}

case "${1:-up}" in
up)
  docker compose up -d
  echo "Stack running"
  ;;
down)
  docker compose down
  ;;
logs)
  docker compose logs -f
  ;;
ps)
  docker compose ps
  ;;
shell)
  docker compose run --rm --no-deps app bash
  ;;
rebuild)
  docker compose up -d --build
  ;;
embed)
  echo "Starting qdrant..."
  docker compose up -d qdrant
  echo "Running ingestion (${MRR_PYTHON})..."
  run_python -m db_ops.embed
  echo "Starting app..."
  docker compose up -d app
  echo "Stack running"
  ;;
*)
  echo "usage: $0 [up|down|logs|ps|shell|rebuild|embed]"
  exit 1
  ;;
esac
