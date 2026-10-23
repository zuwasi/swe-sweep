#!/bin/bash
# Rerun ONLY the 3 quota-truncated claude repos (black, rxjava, proj) after the 16:10 quota
# reset, or sooner if the user switches the CLI to Console/API billing (marker file).
cd /home/danie/mini-swe-sweep
LOG=logs/pipeline.log
THREE="black rxjava proj"
log() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; }

log "run2f waiting for ~/.claude_console marker or 16:11 quota reset"
while true; do
  [ -f "$HOME/.claude_console" ] && { log "marker file found, starting early"; break; }
  [ "$(date +%H:%M)" \> "16:11" ] && { log "16:11 reached, starting on fresh quota"; break; }
  sleep 20
done

export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$PATH"
REPLY=$(cd /tmp && timeout 120 claude -p "Reply with exactly: OK" --model claude-opus-5-5 2>&1 | tail -1)
log "claude CLI check replied: $REPLY"
if [ "$REPLY" != "OK" ]; then
  log "ERROR: claude CLI check failed, NOT starting. Output: $REPLY"
  exit 1
fi

for r in $THREE; do
  nohup ./run_agent.sh claude "$r" > "logs/run-claude-$r.out" 2>&1 &
  log "launched claude $r (pid $!)"
  sleep 5
done

for i in $(seq 1 240); do
  if ! pgrep -f "run_agent.sh claude" > /dev/null; then break; fi
  sleep 30
done
log "claude 3-repo rerun sessions finished"

for r in $THREE; do
  if [ -s "patches/claude__$r.diff" ]; then
    log "claude patch $r OK ($(wc -l < patches/claude__$r.diff) lines)"
    log "eval start claude/$r"
    if sg docker -c "./eval.sh $r claude" >> logs/evals-run2.log 2>&1; then
      log "eval done claude/$r"
    else
      log "eval FAILED claude/$r"
    fi
  else
    log "ERROR: empty/missing patches/claude__$r.diff, skipping eval"
  fi
done

{
  echo "=== RUN 2 batch 3 CLAUDE 3-repo rerun (black rxjava proj) — $(date) ==="
  for r in $THREE; do
    f=$(ls -t results/jobs-claude-$r/*/swe-sweep__*/verifier/reward.json 2>/dev/null | head -1)
    if [ -n "$f" ]; then
      echo "claude $r $(cat "$f" | tr -d '\n')"
    else
      echo "claude $r MISSING reward.json"
    fi
  done
} >> results-run2-summary.txt
log "run2f complete"
