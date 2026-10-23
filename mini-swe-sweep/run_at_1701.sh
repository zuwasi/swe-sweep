#!/bin/bash
# Wait for the 17:00 quota reset, verify the Claude CLI, then start the batch-3 claude rerun.
cd /home/danie/mini-swe-sweep
LOG=logs/pipeline.log
TARGET="17:01"
log() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; }

# sleep until 17:01 today (if already past, run immediately)
while [ "$(date +%H:%M)" \< "$TARGET" ]; do
  sleep 30
done
log "quota-reset wait over (17:01), verifying claude CLI"

REPLY=$(cd /tmp && timeout 120 claude -p "Reply with exactly: OK" --model claude-opus-5-5 2>&1 | tail -1)
log "claude CLI check replied: $REPLY"
if [ "$REPLY" != "OK" ]; then
  log "ERROR: claude CLI check failed, NOT starting pipeline. Output: $REPLY"
  exit 1
fi

./drive_run2e.sh
