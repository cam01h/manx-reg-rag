#!/usr/bin/env bash
set -euo pipefail

MRR_PYTHON="${MRR_PYTHON:-container}"

run_python() {
  if [ "$MRR_PYTHON" = "host" ]; then
    uv run python "$@"
  else
    docker compose exec app uv run python "$@"
  fi
}

wait_for_qdrant() {
  echo "Waiting for Qdrant..."
  local attempt
  for ((attempt = 0; attempt < 30; attempt++)); do
    if docker compose exec -T qdrant \
      sh -c 'wget -q -O- http://localhost:6333/readyz >/dev/null 2>&1'; then
      echo "Qdrant ready"
      return 0
    fi
    sleep 2
  done
  echo "Qdrant did not become ready in 60s" >&2
  return 1
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
  docker compose exec app bash
  ;;
rebuild)
  docker compose up -d --build
  ;;
embed)
  echo "Ensuring stack is up..."
  docker compose up -d
  wait_for_qdrant
  echo "Running ingestion (${MRR_PYTHON})..."
  run_python -m db_ops.embed
  ;;
*)
  echo "usage: $0 [up|down|logs|ps|shell|rebuild|embed]"
  exit 1
  ;;
esac
