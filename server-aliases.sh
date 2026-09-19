MRR=/opt/manx-reg-rag

alias mrr='cd $MRR'
alias deploy='cd $MRR && git pull && ./mrr.sh rebuild'
alias mem='docker compose -f $MRR/docker-compose.yml exec app sh -c "
for p in /proc/[0-9]*; do
  [ \"\$(cat \$p/comm 2>/dev/null)\" = uvicorn ] && \
    grep -E \"^(Rss|Anonymous|Swap)\" \$p/smaps_rollup
done"'
