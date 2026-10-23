#!/bin/bash
# Batch-3 claude-only rerun: previous two claude arms were killed by the Claude
# monthly spend limit. Quota verified available before launch.
# Guards: never eval an empty/missing diff (that crashes the verifier).
set -u
cd /home/danie/mini-swe-sweep
ALL="hdf5 proj black rxjava fsharp syn"
LOG=logs/pipeline.log
log() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; }

log "run2e (claude-only batch3 rerun) started"

for r in $ALL; do
  nohup ./run_agent.sh claude "$r" > "logs/run-claude-$r.out" 2>&1 &
  log "launched claude $r (pid $!)"
  sleep 5
done

for i in $(seq 1 240); do
  if ! pgrep -f "run_agent.sh claude" > /dev/null; then break; fi
  sleep 30
done
log "claude batch3 rerun2 sessions finished"

for r in $ALL; do
  if [ -s "patches/claude__$r.diff" ]; then
    log "claude patch $r OK ($(wc -l < patches/claude__$r.diff) lines)"
  else
    log "ERROR: empty or missing patches/claude__$r.diff — session truncated, skipping eval for $r"
  fi
done

for r in $ALL; do
  if [ -s "patches/claude__$r.diff" ]; then
    log "eval start claude/$r"
    if sg docker -c "./eval.sh $r claude" >> logs/evals-run2.log 2>&1; then
      log "eval done claude/$r"
    else
      log "eval FAILED claude/$r (see logs/evals-run2.log)"
    fi
  fi
done

{
  echo "=== RUN 2 batch 3 CLAUDE RERUN2 (hdf5 proj black rxjava fsharp syn) — $(date) ==="
  for r in $ALL; do
    f=$(ls -t results/jobs-claude-$r/*/swe-sweep__*/verifier/reward.json 2>/dev/null | head -1)
    if [ -n "$f" ]; then
      echo "claude $r $(cat "$f" | tr -d '\n')"
    else
      echo "claude $r MISSING reward.json"
    fi
  done
} >> results-run2-summary.txt
log "run2e pipeline complete"
