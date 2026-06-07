#!/usr/bin/env bash
set -euo pipefail

case "${1:-up}" in
up)
  docker compose up -d
  echo "Stack running at http://localhost:8000"
  ;;
down)
  docker compose down
  ;;
logs)
  docker compose logs -f
  ;;
rebuild)
  docker compose up -d --build
  ;;
ingest)
  echo "Ensuring stack is up..."
  docker compose up -d
  echo "Running ingestion..."
  uv run python -m db_ops.embeddings
  ;;
*)
  echo "usage: $0 [up|down|logs|rebuild|ingest]"
  exit 1
  ;;
esac
