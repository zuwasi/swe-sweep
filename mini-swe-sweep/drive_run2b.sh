#!/bin/bash
# Pipeline extension for the 2 added repos (z3 = C++, tokio = Rust), same-model run.
# 1. Wait for amp z3/tokio. 2. Launch claude z3/tokio. 3. Wait. 4. Run 4 evals. 5. Append scores.
set -u
cd /home/danie/mini-swe-sweep
LOG=logs/pipeline.log
log() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; }

log "run2b (z3, tokio) pipeline started"

for i in $(seq 1 180); do
  if ! pgrep -f "run_agent.sh amp" > /dev/null; then break; fi
  sleep 30
done
log "amp z3/tokio sessions finished"
for r in z3 tokio; do
  if [ -s "patches/amp__$r.diff" ]; then log "amp patch $r OK ($(wc -l < patches/amp__$r.diff) lines)"; else log "ERROR: missing patches/amp__$r.diff"; fi
done

for r in z3 tokio; do
  nohup ./run_agent.sh claude "$r" > "logs/run-claude-$r.out" 2>&1 &
  log "launched claude $r (pid $!)"
  sleep 5
done

for i in $(seq 1 240); do
  if ! pgrep -f "run_agent.sh claude" > /dev/null; then break; fi
  sleep 30
done
log "claude z3/tokio sessions finished"
for r in z3 tokio; do
  if [ -s "patches/claude__$r.diff" ]; then log "claude patch $r OK ($(wc -l < patches/claude__$r.diff) lines)"; else log "ERROR: missing patches/claude__$r.diff"; fi
done

for agent in amp claude; do
  for r in z3 tokio; do
    log "eval start $agent/$r"
    if sg docker -c "./eval.sh $r $agent" >> logs/evals-run2.log 2>&1; then
      log "eval done $agent/$r"
    else
      log "eval FAILED $agent/$r (see logs/evals-run2.log)"
    fi
  done
done

{
  echo "=== RUN 2 additions (z3, tokio) — $(date) ==="
  for agent in amp claude; do
    for r in z3 tokio; do
      f=$(ls -t results/jobs-$agent-$r/*/swe-sweep__*/verifier/reward.json 2>/dev/null | head -1)
      if [ -n "$f" ]; then
        echo "$agent $r $(cat "$f" | tr -d '\n')"
      else
        echo "$agent $r MISSING reward.json"
      fi
    done
  done
} >> results-run2-summary.txt
log "run2b pipeline complete"
