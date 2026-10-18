# requires MRR exported in .bashrc, e.g. export MRR=/opt/manx-reg-rag

# ====================
# <==  mrr commands  ==>
# ====================
# clears the old `alias mrr` if this file is re-sourced in an older shell
unalias mrr 2>/dev/null || true

# everything in mrr.sh: mrr up | down | pd | embed | diag | deploy ...  (mrr help)
mrr() { "$MRR/mrr.sh" "$@"; }

# jump to the repo
alias cdm='cd "$MRR"'

# shortcuts
alias diag='mrr diag'
alias deploy='mrr deploy && source ~/.bashrc'

# ====================
# <== server tools ==>
# ====================
# get RAM allocation
alias mem='docker compose --project-directory "$MRR" exec app sh -c "
for p in /proc/[0-9]*; do
  [ \"\$(cat \$p/comm 2>/dev/null)\" = uvicorn ] && \
    grep -E \"^(Rss|Anonymous|Swap)\" \$p/smaps_rollup
done"'

# live logs: log-l [lines] [service...]
log-l() {
  local n="${1:-20}"
  echo "running live logs"
  docker compose --project-directory "$MRR" logs -f --tail="$n" "${@:2}"
}

# grep logs: logs-g <term> [lines]
logs-g() {
  local t="$1"
  local n="${2:-20}"
  echo "grep logs for: $t"
  docker compose --project-directory "$MRR" logs | grep -- "$t" | tail -n "$n"
}

# ====================
# <==     tmux     ==>
# ====================
alias main='tmux a -t main'
alias dev='tmux a -t dev'
