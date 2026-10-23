#!/bin/bash
# Batch-3 rerun: the original batch3 amp sessions were lost to a corrupted script
# (edited while running) and the claude sessions to the Claude spend limit.
# Rerun amp on the 5 broken repos (fsharp amp is already valid), then claude on all 6,
# then evals. DO NOT EDIT run_agent.sh while this script is running.
set -u
cd /home/danie/mini-swe-sweep
AMP_REPOS="hdf5 proj black rxjava syn"
ALL="hdf5 proj black rxjava fsharp syn"
LOG=logs/pipeline.log
log() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; }

wait_repos() {
  for i in $(seq 1 240); do
    busy=0
    for r in $ALL; do
      if pgrep -f "run_agent.sh (amp|claude) $r" > /dev/null; then busy=1; break; fi
    done
    [ $busy -eq 0 ] && return 0
    sleep 30
  done
  return 0
}

log "run2d (batch3 rerun) started"

for r in $AMP_REPOS; do
  nohup ./run_agent.sh amp "$r" > "logs/run-amp-$r.out" 2>&1 &
  log "launched amp $r (pid $!)"
  sleep 5
done

wait_repos
log "amp batch3 rerun sessions finished"
ok=1
for r in $AMP_REPOS; do
  if [ -s "patches/amp__$r.diff" ]; then log "amp patch $r OK ($(wc -l < patches/amp__$r.diff) lines)"; else log "ERROR: missing patches/amp__$r.diff"; ok=0; fi
done

for r in $ALL; do
  nohup ./run_agent.sh claude "$r" > "logs/run-claude-$r.out" 2>&1 &
  log "launched claude $r (pid $!)"
  sleep 5
done

wait_repos
log "claude batch3 rerun sessions finished"
for r in $ALL; do
  if [ -s "patches/claude__$r.diff" ]; then log "claude patch $r OK ($(wc -l < patches/claude__$r.diff) lines)"; else log "ERROR: missing patches/claude__$r.diff"; fi
done

for agent in amp claude; do
  for r in $ALL; do
    [ "$agent-$r" = "amp-fsharp" ] && continue  # already evaluated (0/5), keep
    log "eval start $agent/$r"
    if sg docker -c "./eval.sh $r $agent" >> logs/evals-run2.log 2>&1; then
      log "eval done $agent/$r"
    else
      log "eval FAILED $agent/$r (see logs/evals-run2.log)"
    fi
  done
done

{
  echo "=== RUN 2 batch 3 RERUN (hdf5 proj black rxjava fsharp syn) — $(date) ==="
  for agent in amp claude; do
    for r in $ALL; do
      f=$(ls -t results/jobs-$agent-$r/*/swe-sweep__*/verifier/reward.json 2>/dev/null | head -1)
      if [ -n "$f" ]; then
        echo "$agent $r $(cat "$f" | tr -d '\n')"
      else
        echo "$agent $r MISSING reward.json"
      fi
    done
  done
} >> results-run2-summary.txt
log "run2d pipeline complete"
