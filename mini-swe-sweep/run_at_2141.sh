#!/bin/bash
# Third claude-arm rerun, waiting for tonight's 21:40 spend-limit reset.
cd /home/danie/mini-swe-sweep
LOG=logs/pipeline.log
TARGET="21:41"
log() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; }

while [ "$(date +%H:%M)" \< "$TARGET" ]; do
  sleep 30
done
log "21:41 reached, verifying claude CLI"

REPLY=$(cd /tmp && timeout 120 claude -p "Reply with exactly: OK" --model claude-opus-5-5 2>&1 | tail -1)
log "claude CLI check replied: $REPLY"
if [ "$REPLY" != "OK" ]; then
  log "ERROR: claude CLI check failed, NOT starting. Output: $REPLY"
  exit 1
fi

# Remove stale eval results from truncated sessions so only fresh scores exist
for r in hdf5 proj black rxjava fsharp syn; do
  rm -rf "results/jobs-claude-$r"
done
log "stale claude eval results cleared, starting drive_run2e.sh"

./drive_run2e.sh
