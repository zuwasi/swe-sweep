#!/bin/bash
# Start the batch-3 claude arm as soon as the API key file appears (API billing, no monthly cap).
# Fallback: if no key file by 21:41, proceed on the subscription quota reset instead.
# Clears stale eval results first. Verifies the CLI before launching.
cd /home/danie/mini-swe-sweep
LOG=logs/pipeline.log
log() { echo "[$(date '+%H:%M:%S')] $*" >> "$LOG"; }

log "waiting for ~/.claude_api_key (fallback: quota-reset path at 21:41)"
while [ ! -f "$HOME/.claude_api_key" ]; do
  if [ "$(date +%H:%M)" \> "21:41" ]; then break; fi
  sleep 20
done

export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$PATH"
if [ -f "$HOME/.claude_api_key" ]; then
  . "$HOME/.claude_api_key"
  log "API key file found, verifying claude CLI on API billing"
  REPLY=$(cd /tmp && timeout 120 claude -p "Reply with exactly: OK" --model claude-opus-5-5 2>&1 | tail -1)
  log "claude CLI check replied: $REPLY"
  if [ "$REPLY" != "OK" ]; then
    log "ERROR: claude CLI check failed with API key, NOT starting. Output: $REPLY"
    exit 1
  fi
else
  log "no API key file by 21:41, falling back to quota-reset verification"
  REPLY=$(cd /tmp && timeout 120 claude -p "Reply with exactly: OK" --model claude-opus-5-5 2>&1 | tail -1)
  log "claude CLI check replied: $REPLY"
  if [ "$REPLY" != "OK" ]; then
    log "ERROR: claude CLI check failed on subscription, NOT starting. Output: $REPLY"
    exit 1
  fi
fi

for r in hdf5 proj black rxjava fsharp syn; do
  rm -rf "results/jobs-claude-$r"
done
log "stale claude eval results cleared, starting drive_run2e.sh"
./drive_run2e.sh
