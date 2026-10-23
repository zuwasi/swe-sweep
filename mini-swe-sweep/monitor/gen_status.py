#!/usr/bin/env python3
"""Generate a real-time status page for the mini-swe_sweep run 2 pipeline."""
import glob
import html
import json
import os
import subprocess
import time

BASE = "/home/danie/mini-swe-sweep"
REPOS = [("libexpat", "C"), ("click", "Python"), ("gson", "Java"), ("roslyn", "C#"), ("z3", "C++"), ("tokio", "Rust"),
         ("hdf5", "C"), ("proj", "C++"), ("black", "Python"), ("rxjava", "Java"), ("fsharp", "C#"), ("syn", "Rust")]
AGENTS = ["amp", "claude"]
OUT = os.path.join(BASE, "monitor", "status.html")


def pgrep(pattern):
    try:
        out = subprocess.run(["pgrep", "-af", pattern], capture_output=True, text=True)
        lines = [l for l in out.stdout.strip().splitlines() if l]
        return len(lines)
    except Exception:
        return 0


def reward(agent, repo):
    hits = sorted(glob.glob(f"{BASE}/results/jobs-{agent}-{repo}/*/swe-sweep__*/verifier/reward.json"))
    if not hits:
        return None
    try:
        with open(hits[-1]) as f:
            return json.load(f)
    except Exception:
        return None


def agent_done(agent):
    # done when patch exists AND no matching run_agent process
    patch_ok = all(os.path.exists(f"{BASE}/patches/{agent}__{r}.diff")
                   and os.path.getsize(f"{BASE}/patches/{agent}__{r}.diff") > 0
                   for r, _ in REPOS)
    return patch_ok and pgrep(f"run_agent.sh {agent}") == 0


rows = []
for agent in AGENTS:
    for repo, lang in REPOS:
        r = reward(agent, repo)
        patch = f"{BASE}/patches/{agent}__{repo}.diff"
        patch_lines = 0
        if os.path.exists(patch):
            with open(patch, "rb") as f:
                patch_lines = sum(1 for _ in f)
        if r:
            score = f"{int(r.get('n_resolved', 0))}/5"
            detail = (f"regressions={int(r.get('n_regressions', 0))}, "
                      f"build_ok={int(r.get('agent_build_ok', 0))}, "
                      f"visible_ok={int(r.get('visible_ok', 0))}")
            color = "#1a7f37" if r.get("reward", 0) >= 0.5 else ("#9a6700" if r.get("reward", 0) > 0 else "#8b0000")
            badge = f"<span style='background:{color};color:#fff;padding:2px 10px;border-radius:10px'>{score}</span>"
            status = "evaluated"
        else:
            badge = "<span style='color:#666'>pending</span>"
            detail = ""
            patch = f"{BASE}/patches/{agent}__{repo}.diff"
            import subprocess as sp
            sess = sp.run(["grep", "-E", f"\\[{agent}/{repo}\\] exit=1", f"{BASE}/logs/sessions.log"],
                          capture_output=True, text=True)
            if sess.returncode == 0 and sess.stdout.strip():
                status = "quota-truncated (no score)"
            elif not os.path.exists(patch) or os.path.getsize(patch) == 0:
                status = "no diff (truncated)"
            else:
                status = "eval queued/running"
        rows.append(f"<tr><td>{agent.upper()}</td><td>{repo}</td><td>{lang}</td>"
                    f"<td>{badge}</td><td>{detail}</td><td>{patch_lines}</td><td>{status}</td></tr>")

total = sum(int(reward(a, r).get("n_resolved", 0)) for a in AGENTS for r, _ in REPOS if reward(a, r))
evaluated = sum(1 for a in AGENTS for r, _ in REPOS if reward(a, r))

with open(f"{BASE}/logs/pipeline.log") as f:
    pipe_log = "".join(f"<div>{html.escape(l.rstrip())}</div>" for l in f.readlines()[-40:])

amp_running = pgrep(r"run_agent.sh amp")
claude_running = pgrep(r"run_agent.sh claude")
pipeline_running = pgrep("drive_run2.sh")

now = time.strftime("%H:%M:%S")
phase = "running" if pipeline_running else "finished/stopped"
running_html = f"""
<p><b>Pipeline:</b> {phase} &nbsp;|&nbsp; <b>Amp agent sessions running:</b> {amp_running} &nbsp;|&nbsp;
<b>Claude agent sessions running:</b> {claude_running} &nbsp;|&nbsp;
<b>Evals evaluated:</b> {evaluated}/24 &nbsp;|&nbsp; <b>Score so far:</b> amp+claude = {total} bugs resolved</p>
"""

page = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>mini-swe_sweep run 2 live status</title>
<meta http-equiv="refresh" content="60">
<style>
body {{ font-family: sans-serif; margin: 24px; background: #0d1117; color: #e6edf3; }}
h1 {{ font-size: 1.3em; }}
table {{ border-collapse: collapse; margin: 16px 0; }}
td, th {{ border: 1px solid #30363d; padding: 6px 14px; text-align: left; }}
th {{ background: #161b22; }}
#log {{ background: #010409; border: 1px solid #30363d; padding: 12px; font-family: monospace;
        font-size: 0.85em; max-height: 480px; overflow-y: auto; line-height: 1.5; }}
</style></head><body>
<h1>mini-swe_sweep run 2 (same model: claude-opus-5-5 on both arms) - live status</h1>
<p>Auto-refreshes every 60 seconds. Last updated: {now}</p>
{running_html}
<table><tr><th>Agent</th><th>Repo</th><th>Language</th><th>Bugs resolved</th><th>Detail</th><th>Patch lines</th><th>Status</th></tr>
{''.join(rows)}
</table>
<h2>Pipeline log (events)</h2>
<div id="log">{pipe_log}</div>
</body></html>"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    f.write(page)
print(f"wrote {OUT}")
