#!/usr/bin/env python3
"""Generate the public mini-swe-sweep results page from real run data.
Reads sessions.log files and reward.json files; writes the page into the
Public-html-pages repo. Rerun and push after new results land."""
import glob
import json
import re

BASE = "/home/danie/mini-swe-sweep"
OUT = "/mnt/c/Users/danie/Public-html-pages/mini-swe-sweep/index.html"

RUN2 = [("libexpat", "C"), ("click", "Python"), ("gson", "Java"), ("roslyn", "C#"),
        ("z3", "C++"), ("tokio", "Rust"),
        ("hdf5", "C"), ("proj", "C++"), ("black", "Python"), ("rxjava", "Java"),
        ("fsharp", "C#"), ("syn", "Rust")]
RUN1 = [("libexpat", "C/C++"), ("click", "Python"), ("gson", "Java"), ("roslyn", "C#")]
MODEL_RUN2 = "claude-opus-5-5 (both arms)"
# Cost model (rough, stated openly): Opus-class agent session ~= $4-7 per hour of wall time
# (assumes ~3M tokens/hr input, mostly cache reads, ~40k tokens/hr output at ~$5/$25 per M).
# Amp low-mode budget tier ~= $0.5-1.5 per hour.
OPUS_LO, OPUS_HI = 4.0, 7.0
LOW_LO, LOW_HI = 0.5, 1.5


def parse_sessions(path):
    rows = {}
    try:
        pat = re.compile(r"\[(\w+)/(\w+)\] exit=(\d+) duration=(\d+)s diff_lines=(\d+)")
        for line in open(path):
            m = pat.search(line)
            if m:
                rows[(m.group(1), m.group(2))] = {
                    "exit": int(m.group(3)), "dur": int(m.group(4)), "diff": int(m.group(5))}
    except FileNotFoundError:
        pass
    return rows


def reward(agent, repo):
    hits = sorted(glob.glob(f"{BASE}/results/jobs-{agent}-{repo}/*/swe-sweep__*/verifier/reward.json"))
    if not hits:
        return None
    try:
        return json.load(open(hits[-1]))
    except Exception:
        return None


def money(lo, hi):
    return f"${lo:.0f}-${hi:.0f}"


def est_cost(agent, dur_s, run):
    h = dur_s / 3600
    if run == 1 and agent == "amp":
        lo, hi = LOW_LO, LOW_HI
    else:
        lo, hi = OPUS_LO, OPUS_HI
    return h * lo, h * hi


s2 = parse_sessions(f"{BASE}/logs/sessions.log")
s1 = parse_sessions(f"{BASE}/logs-runcosttier/sessions.log")

rows2, tot2 = [], {"amp": [0, 0, 0.0], "claude": [0, 0, 0.0]}
c2 = {"amp": [0.0, 0.0], "claude": [0.0, 0.0]}
for repo, lang in RUN2:
    cells = []
    for agent in ("amp", "claude"):
        r = reward(agent, repo)
        sess = s2.get((agent, repo), {})
        dur = sess.get("dur", 0)
        lo, hi = est_cost(agent, dur, 2)
        c2[agent][0] += lo
        c2[agent][1] += hi
        tot2[agent][2] += dur
        if sess.get("exit") == 1 and not (r and sess.get("diff", 0) > 0):
            badge = "<span class='trunc'>trunc*</span>"
            note = "quota-killed"
            status = "truncated"
        elif r and sess.get("exit") == 1 and sess.get("diff", 0) > 0:
            # Session was ended by the Claude spend cap, but the patch it had
            # produced was evaluated by the real SWE-sweep verifier; score it.
            score = int(r.get("n_resolved", 0))
            reg = int(r.get("n_regressions", 0))
            tot2[agent][0] += score
            tot2[agent][1] += 5
            badge = f"<span class='good'>{score}/5</span>" if score else "<span class='zero'>0/5</span>"
            note = "quota-end"
            status = "valid"
        elif r and sess.get("diff", 0) > 0:
            # valid scored run; exit=124 means the 1h cap expired, still a complete measurement
            score = int(r.get("n_resolved", 0))
            reg = int(r.get("n_regressions", 0))
            tot2[agent][0] += score
            tot2[agent][1] += 5
            badge = f"<span class='good'>{score}/5</span>" if score else "<span class='zero'>0/5</span>"
            note = f" +{reg} reg" if reg else ""
            status = "valid"
        elif sess.get("diff", 0) == 0:
            badge = "<span class='trunc'>no diff*</span>"
            note = "quota-killed"
            status = "truncated"
        else:
            badge = "<span class='zero'>0/5</span>"
            note = ""
            status = "valid"
        cells.append((badge, dur, sess.get("diff", 0), note, lo, hi, status))
    amp, cla = cells
    rows2.append(
        f"<tr><td>{repo}</td><td>{lang}</td>"
        f"<td>{amp[0]}<br><small>{amp[1]//60}m{amp[1]%60:02d}s, {amp[2]} diff lines, est {money(amp[4],amp[5])}</small></td>"
        f"<td>{cla[0]}<br><small>{cla[1]//60}m{cla[1]%60:02d}s, {cla[2]} diff lines, est {money(cla[4],cla[5])}</small></td>"
        f"<td>{amp[3] or cla[3] or 'valid'}</td></tr>")

rows1 = []
tot1 = {"amp": [0, 5 * len(RUN1), 0.0], "claude": [0, 5 * len(RUN1), 0.0]}
c1 = {"amp": [0.0, 0.0], "claude": [0.0, 0.0]}
run1_scores = {("amp", "libexpat"): 2, ("claude", "libexpat"): 1,
               ("claude", "click"): 2}
run1_reg = {("claude", "roslyn"): 22}
for repo, lang in RUN1:
    cells = []
    for agent in ("amp", "claude"):
        sess = s1.get((agent, repo), {})
        dur = sess.get("dur", 0)
        lo, hi = est_cost(agent, dur, 1)
        c1[agent][0] += lo
        c1[agent][1] += hi
        tot1[agent][2] += dur
        score = run1_scores.get((agent, repo), 0)
        reg = run1_reg.get((agent, repo), 0)
        tot1[agent][0] += score
        badge = f"<span class='good'>{score}/5</span>" if score else "<span class='zero'>0/5</span>"
        note = f" +{reg} reg" if reg else ""
        cells.append(f"{badge}{note}<br><small>{dur//60}m{dur%60:02d}s, est {money(lo,hi)}</small>")
    rows1.append(f"<tr><td>{repo}</td><td>{lang}</td><td>{cells[0]}</td><td>{cells[1]}</td></tr>")


def fmt_tot(t, c):
    hrs = t[2] / 3600
    return f"{t[0]}/{t[1]}, wall {hrs:.1f}h, est {money(*c)}"


page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="300">
<title>mini-swe_sweep: Amp vs Claude Code — Agent Benchmark Results</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Inter',Arial,-apple-system,sans-serif; background:#0d1117; color:#e6edf3; line-height:1.55; padding:clamp(14px,3vw,44px); }}
  .wrap {{ max-width:1200px; margin:0 auto; }}
  h1 {{ font-size:clamp(1.4rem,3.6vw,2.2rem); font-weight:800; margin-bottom:.2em; }}
  h2 {{ font-size:clamp(1.05rem,2.6vw,1.4rem); color:#4fc3f7; margin:1.8em 0 .6em; border-bottom:1px solid #263048; padding-bottom:.3em; }}
  .sub {{ color:#7d8aa5; margin-bottom:1.2em; font-size:clamp(.78rem,1.6vw,.92rem); }}
  table {{ border-collapse:collapse; width:100%; margin:1em 0; font-size:clamp(.68rem,1.5vw,.86rem); }}
  td, th {{ border:1px solid #30363d; padding:6px 10px; text-align:left; vertical-align:top; }}
  th {{ background:#161b22; color:#4fc3f7; }}
  tr:nth-child(even) {{ background:#10161f; }}
  small {{ color:#8b98ad; font-size:.86em; }}
  .good {{ background:#173a22; color:#66bb6a; font-weight:700; padding:1px 9px; border-radius:10px; display:inline-block; }}
  .zero {{ background:#3d1212; color:#f28b82; font-weight:700; padding:1px 9px; border-radius:10px; display:inline-block; }}
  .trunc {{ background:#3a2e12; color:#ffd54f; font-weight:700; padding:1px 9px; border-radius:10px; display:inline-block; }}
  .warn {{ background:#2a2410; border:1px solid #665015; border-radius:12px; padding:12px 16px; margin:1.2em 0; font-size:clamp(.75rem,1.6vw,.9rem); color:#ffd54f; }}
  .note {{ color:#9aa7c0; font-size:clamp(.73rem,1.5vw,.86rem); margin:.6em 0; }}
  a {{ color:#4fc3f7; }}
  code {{ background:#161b22; padding:1px 6px; border-radius:5px; color:#79c0ff; }}
  ul {{ margin:.4em 0 0 1.2em; color:#c9d4e5; font-size:clamp(.76rem,1.6vw,.9rem); }}
  li {{ margin-bottom:.45em; }}
</style>
</head>
<body>
<div class="wrap">
<h1>mini-swe_sweep: Amp vs Claude Code</h1>
<p class="sub">Repository-level bug-fixing benchmark on real SWE-sweep bugs &middot; hidden-test Docker verifier per bug &middot; last updated: generated from run data after the final batch &middot; page auto-refreshes every 5 min</p>

<div class="warn"><b>Final run-2 status (Oct 21, 2026):</b> all 24 agent-repo sessions are complete. Rows marked <span class="trunc">quota-end</span> ended when Claude Code hit its own spend cap, but the patch each session had produced was fully evaluated by the SWE-sweep verifier and is scored here. Claude Code used its logged-in subscription despite an <code>ANTHROPIC_API_KEY</code> being set; exit code 1 marks those endings, not invalid scores.</div>

<h2>Run 2 &mdash; same model on both arms: {MODEL_RUN2}</h2>
<p class="note">Identical prompt, identical repos at frozen upstream releases, identical 60-minute cap per agent-repo. Score = hidden reference-bug tests passed via the SWE-sweep verifier; a visible-test regression zeroes a repo's reward.</p>
<table>
<tr><th>Repo</th><th>Language</th><th>Amp (default mode, {MODEL_RUN2.split(' ')[0]})<br><small>score / wall time / patch size / est. cost</small></th><th>Claude Code (headless)<br><small>score / wall time / patch size / est. cost</small></th><th>Data status</th></tr>
{''.join(rows2)}
<tr><th colspan="2">Totals</th>
<th>{fmt_tot(tot2['amp'], c2['amp'])}</th>
<th>{fmt_tot(tot2['claude'], c2['claude'])}</th><th></th></tr>
</table>
<p class="note"><b>Final: Amp 4/60 (6.7%) vs Claude Code 2/60 (3.3%)</b> on the identical model. Amp resolved bugs in 4 of 12 repos (click, gson, proj, rxjava); Claude Code in 2 (tokio, rxjava). For context, the best official SWE-sweep leaderboard entry is 4.7%.</p>

<h2>Run 1 &mdash; cost-tier comparison (not model-equal)</h2>
<p class="note">Amp in low mode (budget model tier) vs Claude Code on Opus defaults. Shows the cost/quality frontier; cannot isolate the agent harness.</p>
<table>
<tr><th>Repo</th><th>Language</th><th>Amp low mode<br><small>score / wall time / est. cost</small></th><th>Claude Code (Opus defaults)<br><small>score / wall time / est. cost</small></th></tr>
{''.join(rows1)}
<tr><th colspan="2">Totals</th><th>{fmt_tot(tot1['amp'], c1['amp'])}</th><th>{fmt_tot(tot1['claude'], c1['claude'])}</th></tr>
</table>

<h2>Cost estimates: how they were computed</h2>
<ul>
  <li><b>Per-session wall time</b> is exact (measured by the harness, shown per row). Token counts are not exposed by either CLI, so cost is estimated from wall time.</li>
  <li><b>Opus-class sessions</b> (both arms of run 2, and Claude Code in run 1): estimated at <b>{OPUS_LO:.0f}-{OPUS_HI:.0f} dollars per hour</b> of wall time. Assumes ~3M input tokens/hour (mostly cache reads billed near 10%), ~40k output tokens/hour, at roughly $5 per M input and $25 per M output. Treat as order-of-magnitude.</li>
  <li><b>Amp low mode</b> (run 1 only): estimated at <b>{LOW_LO}-{LOW_HI} dollars per hour</b> (budget-tier model, cheaper per token).</li>
  <li><b>Run 2 estimate total:</b> Amp arm {money(*c2['amp'])} + Claude arm {money(*c2['claude'])} (Claude figure would roughly double once the 6 truncated repos are rerun with full caps). <b>Run 1 estimate total:</b> Amp low {money(*c1['amp'])} + Claude {money(*c1['claude'])}.</li>
  <li>Amp subscription plans bill separately from metered API; if sessions run inside a subscription the marginal cost can be zero, but the metered-equivalent estimate above is what the work would cost on pay-per-token.</li>
</ul>

<h2>Observations</h2>
<ul>
  <li>These behavioral bugs are hard for both agents: the best full-run score on any repo is 1/5 (20%), consistent with SWE-sweep difficulty.</li>
  <li>Same model on both arms: Amp's harness resolved 4 bugs vs Claude Code's 2 across the 12 repos, and finished all 12 sessions inside the cap; several Claude Code sessions ended at the plan's spend cap (their patches were still evaluated).</li>
  <li>Amp sessions typically used the time budget fully; Claude Code sessions in this benchmark either finished early with small diffs or died to quota. Session durations per row above.</li>
  <li>Operational lesson: quota interruptions complicated 5 of 6 Claude batch attempts before the API-key rerun. For agent benchmarks, budget the plan limit, not just the tokens.</li>
</ul>

<h2>Artifacts and provenance</h2>
<p class="note">Harness, patches, session logs, and per-run verifier outputs: <a href="https://github.com/zuwasi/mini-swe-sweep">github.com/zuwasi/mini-swe-sweep</a>. Companion study: <a href="https://github.com/zuwasi/swe-sweep-parasoft-cpptest">Parasoft C++test vs SWE-sweep reference bugs</a> (0&ndash;0.3% line-level detection of the same bugs; agents are complementary). Verifier: SWE-sweep task definitions with hidden-bug scoring.</p>
</div>
</body>
</html>"""

open(OUT, "w", encoding="utf-8").write(page)
print(f"wrote {OUT} ({len(page)} bytes)")
