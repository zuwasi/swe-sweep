#!/bin/bash
# Pipeline extension batch 3: six more repos, one per language (C, C++, Python, Java, C#, Rust).
# 1. Wait for amp sessions on the new repos. 2. Launch claude sessions. 3. Wait. 4. Run 12 evals. 5. Append scores.
set -u
cd /home/danie/mini-swe-sweep
NEW="hdf5 proj black rxjava fsharp syn"
LOG=logs/pipeline.log
log() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; }

# Wait until no other run_agent.sh session is on THESE repos (other pipelines may use other repos)
wait_repos() {
  for i in $(seq 1 240); do
    busy=0
    for r in $NEW; do
      if pgrep -f "run_agent.sh (amp|claude) $r" > /dev/null; then busy=1; break; fi
    done
    [ $busy -eq 0 ] && return 0
    sleep 30
  done
  return 0
}

log "run2c (hdf5 proj black rxjava fsharp syn) pipeline started"

for r in $NEW; do
  nohup ./run_agent.sh amp "$r" > "logs/run-amp-$r.out" 2>&1 &
  log "launched amp $r (pid $!)"
  sleep 5
done

wait_repos
log "amp batch3 sessions finished"
for r in $NEW; do
  if [ -s "patches/amp__$r.diff" ]; then log "amp patch $r OK ($(wc -l < patches/amp__$r.diff) lines)"; else log "ERROR: missing patches/amp__$r.diff"; fi
done

for r in $NEW; do
  nohup ./run_agent.sh claude "$r" > "logs/run-claude-$r.out" 2>&1 &
  log "launched claude $r (pid $!)"
  sleep 5
done

wait_repos
log "claude batch3 sessions finished"
for r in $NEW; do
  if [ -s "patches/claude__$r.diff" ]; then log "claude patch $r OK ($(wc -l < patches/claude__$r.diff) lines)"; else log "ERROR: missing patches/claude__$r.diff"; fi
done

for agent in amp claude; do
  for r in $NEW; do
    log "eval start $agent/$r"
    if sg docker -c "./eval.sh $r $agent" >> logs/evals-run2.log 2>&1; then
      log "eval done $agent/$r"
    else
      log "eval FAILED $agent/$r (see logs/evals-run2.log)"
    fi
  done
done

{
  echo "=== RUN 2 batch 3 (hdf5 proj black rxjava fsharp syn) — $(date) ==="
  for agent in amp claude; do
    for r in $NEW; do
      f=$(ls -t results/jobs-$agent-$r/*/swe-sweep__*/verifier/reward.json 2>/dev/null | head -1)
      if [ -n "$f" ]; then
        echo "$agent $r $(cat "$f" | tr -d '\n')"
      else
        echo "$agent $r MISSING reward.json"
      fi
    done
  done
} >> results-run2-summary.txt
log "run2c pipeline complete"
