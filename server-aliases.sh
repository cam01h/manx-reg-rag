# define $MRR in your .bashrc with a path

# ====================
# <== server tools ==>
# ====================
alias mrr='cd $MRR'

# git pull and and docker compose rebuild
alias deploy='cd $MRR && git pull && ./mrr.sh rebuild'

# get RAM allocation
alias mem='docker compose -f $MRR/docker-compose.yml exec app sh -c "
for p in /proc/[0-9]*; do
  [ \"\$(cat \$p/comm 2>/dev/null)\" = uvicorn ] && \
    grep -E \"^(Rss|Anonymous|Swap)\" \$p/smaps_rollup
done"'

# ====================
# <==     tmux     ==>
# ====================
alias main='tmux a -t main'
alias dev='tmux a -t dev'
log-l() {
  local n="${1:-20}"
  echo "running live logs"
  docker compose --project-directory "$MRR" logs -f --tail="$n" "${@:2}"
}

logs-g() {
  local t="$1"
  local n="${2:-20}"
  echo "grep logs for: $t"
  docker compose --project-directory "$MRR" logs | grep -- "$t" | tail -n "$n"
}

# diagnostics cli
diag() { (cd "$MRR" && uv run python -m tests.extraction_ops.diagnostics.cli "$@"); }

# process documents
alias mrr-pd='uv run python -m extraction_ops.process_documents'

# qdrant embed
alias mrr-embed='(cd "$MRR" && ./mrr.sh embed)'
