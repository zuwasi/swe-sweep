#!/usr/bin/env python3
"""Line-level overlap check for z3: do C++test finding lines fall on base-side
lines changed by the 11 SWE-sweep reference fix commits (subtask ids)?
Ground truth: tests/swesweep_eval.json subtask ids = upstream fix commit prefixes.
"""
import glob
import html
import json
import os
import re
import subprocess
from collections import defaultdict

REPO = "/home/danie/swe-cpptest/tarantool"
EVAL = "/mnt/c/Users/danie/amp-demos/swe-sweep/tasks/swe-sweep__tarantool/tests/swesweep_eval.json"
ORACLE = "/mnt/c/Users/danie/amp-demos/swe-sweep/tasks/swe-sweep__tarantool/tests/oracle"


def sh(*args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw).stdout


def run(*args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


# 1. Collect base-side changed lines from the oracle fix patches
subtasks = json.load(open(EVAL))["subtasks"]
fix_lines = defaultdict(set)
used = []
for st in subtasks:
    patch = open(os.path.join(ORACLE, f"{st['id']}.patch"), encoding="utf-8", errors="replace").read()
    cur = None
    for dl in patch.splitlines():
        if dl.startswith("--- a/"):
            cur = dl[6:]
        elif dl.startswith("@@") and cur:
            m = re.search(r"-(\d+)(?:,(\d+))?", dl)
            if m:
                start = int(m.group(1))
                n = int(m.group(2)) if m.group(2) is not None else 1
                for ln in range(start, start + max(n, 1)):
                    fix_lines[cur].add(ln)
    used.append(st["id"])

print(f"fix commits used: {len(used)}/{len(subtasks)}")

# 2. Extract findings (cfg, file, line, rule) from dev reports
FIND = "/home/danie/swe-cpptest/tarantool"
findings = []
for cfg_dir in glob.glob(f"{FIND}/report-*"):
    reps = glob.glob(f"{cfg_dir}/report*_dev1.html")
    if not reps:
        continue
    rep = max(reps, key=os.path.getmtime)
    cfg = os.path.basename(cfg_dir)
    h = open(rep, encoding="utf-8", errors="replace").read()
    txt = re.sub(r"<[^>]+>", "|", h)
    txt = html.unescape(txt)
    txt = re.sub(r"\|+", "|", txt)
    pieces = re.split(r"(\|/?[\w.+-]+(?:/[\w.+-]+)*\.(?:c|cc|cpp|h|hpp|cxx)\|)", txt)
    TOKEN = re.compile(r"\|(\d+):[\s\xa0]*\||\|\(?([A-Za-z][A-Za-z0-9]*(?:[._-][A-Za-z0-9]+)+)\)?\|")
    for p in pieces:
        if re.fullmatch(r"\|/?[\w.+-]+(?:/[\w.+-]+)*\.(?:c|cc|cpp|h|hpp|cxx)\|", p):
            cur = p.strip("|")
            continue
        pending_line = None
        for tm in TOKEN.finditer(p):
            if tm.group(1):
                pending_line = int(tm.group(1))
            elif pending_line:
                tok = tm.group(2)
                if re.search(r"\d", tok) or tok.startswith(("BD-", "MISRA", "CERT", "METRIC")):
                    findings.append((cfg, cur, pending_line, tok))

print(f"findings parsed: {len(findings)}")

# 3. Overlap + baseline
total_fix = sum(len(v) for v in fix_lines.values())
print(f"total base-side changed lines across fix commits: {total_fix}")
for cfg in sorted({f[0] for f in findings}):
    cfg_f = [f for f in findings if f[0] == cfg]
    hit = [f for f in cfg_f if any(
        f[2] in lns or f[2] - 1 in lns
        for p, lns in fix_lines.items()
        if os.path.basename(p) == os.path.basename(f[1])
    )]
    rules = defaultdict(int)
    for f in hit:
        rules[f[3]] += 1
    pct = 100 * len(hit) / max(len(cfg_f), 1)
    print(f"[{cfg}] line-level hits: {len(hit)}/{len(cfg_f)} ({pct:.1f}%)  {dict(rules)}")
