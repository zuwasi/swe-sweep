#!/bin/bash
# Self-driving pipeline for run 2 (same-model, claude-opus-5-5 both arms).
# 1. Wait for amp sessions to finish. 2. Launch claude sessions. 3. Wait. 4. Run all 8 evals. 5. Collect scores.
set -u
cd /home/danie/mini-swe-sweep
REPOS="libexpat click gson roslyn"
LOG=logs/pipeline.log
log() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; }

log "pipeline started"

# 1. Wait for amp run_agent.sh processes to exit (max 90 min)
for i in $(seq 1 180); do
  if ! pgrep -f "run_agent.sh amp" > /dev/null; then break; fi
  sleep 30
done
if pgrep -f "run_agent.sh amp" > /dev/null; then
  log "WARNING: amp sessions still running after 90min wait, continuing anyway"
else
  log "amp sessions finished"
fi

for r in $REPOS; do
  if [ -s "patches/amp__$r.diff" ]; then log "amp patch $r OK ($(wc -l < patches/amp__$r.diff) lines)"; else log "ERROR: missing patches/amp__$r.diff"; fi
done

# 2. Launch claude sessions (one per repo, concurrent; different repos is safe)
for r in $REPOS; do
  nohup ./run_agent.sh claude "$r" > "logs/run-claude-$r.out" 2>&1 &
  log "launched claude $r (pid $!)"
  sleep 5
done

# 3. Wait for claude sessions (max 2h)
for i in $(seq 1 240); do
  if ! pgrep -f "run_agent.sh claude" > /dev/null; then break; fi
  sleep 30
done
if pgrep -f "run_agent.sh claude" > /dev/null; then
  log "WARNING: claude sessions still running after 2h wait, continuing anyway"
else
  log "claude sessions finished"
fi

for r in $REPOS; do
  if [ -s "patches/claude__$r.diff" ]; then log "claude patch $r OK ($(wc -l < patches/claude__$r.diff) lines)"; else log "ERROR: missing patches/claude__$r.diff"; fi
done

# 4. Run all 8 evals sequentially
for agent in amp claude; do
  for r in $REPOS; do
    log "eval start $agent/$r"
    if sg docker -c "./eval.sh $r $agent" >> logs/evals-run2.log 2>&1; then
      log "eval done $agent/$r"
    else
      log "eval FAILED $agent/$r (see logs/evals-run2.log)"
    fi
  done
done

# 5. Collect scores
{
  echo "=== RUN 2 (same model: claude-opus-5-5 both arms) — $(date) ==="
  for agent in amp claude; do
    for r in $REPOS; do
      f=$(ls -t results/jobs-$agent-$r/*/swe-sweep__*/verifier/reward.json 2>/dev/null | head -1)
      if [ -n "$f" ]; then
        echo "$agent $r $(cat "$f" | tr -d '\n' )"
      else
        echo "$agent $r MISSING reward.json"
      fi
    done
  done
} > results-run2-summary.txt
log "pipeline complete, see results-run2-summary.txt"
