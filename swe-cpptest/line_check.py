#!/usr/bin/env python3
"""Line-level overlap check for libexpat: do C++test finding lines fall inside
regions that upstream later fixed (changed lines on the base side of post-2.4.3
fix commits to expat/lib)?
"""
import html
import re
import subprocess
from collections import defaultdict

REPO = "/home/danie/swe-cpptest/libexpat-full"
BASE = "R_2_4_3"

FIX_SUBJECT = re.compile(r"fix|leak|corrupt|suspend|overflow|crash|oom|out of bounds|use-after", re.I)
SKIP_SUBJECT = re.compile(r"bump|sync file|typo|style|parenthes|cppcheck|mingw|def file|docs?", re.I)

def sh(*args):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True).stdout

# 1. Collect fix commits and their base-side changed lines per file
fix_lines = defaultdict(set)
commits = sh("git", "log", "--no-merges", "--format=%H %s", f"{BASE}..R_2_5_0", "--", "expat/lib").splitlines()
used = []
for line in commits:
    h, subject = line.split(" ", 1)
    if SKIP_SUBJECT.search(subject):
        continue
    if not FIX_SUBJECT.search(subject):
        continue
    diff = sh("git", "diff", BASE, h, "--", "expat/lib")
    used.append(subject)
    cur = None
    for dl in diff.splitlines():
        if dl.startswith("+++ b/"):
            cur = dl[6:]
        elif dl.startswith("--- a/"):
            old = dl[6:]
        elif dl.startswith("@@") and cur:
            m = re.search(r"-(\d+)(?:,(\d+))?", dl)
            if m:
                start = int(m.group(1))
                n = int(m.group(2)) if m.group(2) is not None else 1
                # old-side region: apply to the pre-image file (--- a/)
                pre = old
                for ln in range(start, start + max(n, 1)):
                    fix_lines[pre].add(ln)

print(f"fix commits used: {len(used)}")
for s in used:
    print("  -", s)
print()
for f, lns in fix_lines.items():
    print(f"  {f}: {len(lns)} base-side changed lines")

# 2. Extract findings (file, line, rule) from dev reports
FIND = "/home/danie/swe-cpptest/libexpat"
SECTION = re.compile(r"\|(/?[\w.+-]+(?:/[\w.+-]+)*\.(?:c|cc|cpp|h|hpp|cxx))\|")
RULE = re.compile(r"\|\(?([A-Z][A-Z0-9]+(?:[._-][A-Z0-9]+)+)\)?\|")
LINE = re.compile(r"\|(\d+):? \|")

import glob
import os
findings = []
for cfg_dir in glob.glob(f"{FIND}/report-*"):
    reps = glob.glob(f"{cfg_dir}/report*_dev1.html")
    if not reps:
        continue
    rep = max(reps, key=os.path.getmtime)
    cfg = cfg_dir.split("/report-")[1].split("/")[0]
    h = open(rep, encoding="utf-8", errors="replace").read()
    txt = re.sub(r"<[^>]+>", "|", h)
    txt = html.unescape(txt)
    txt = re.sub(r"\|+", "|", txt)
    pieces = re.split(r"(\|/?[\w.+-]+(?:/[\w.+-]+)*\.(?:c|cc|cpp|h|hpp|cxx)\|)", txt)
    cur = None
    TOKEN = re.compile(r"\|(\d+):[\s\xa0]*\||\|\(?([A-Za-z][A-Za-z0-9]*(?:[._-][A-Za-z0-9]+)+)\)?\|")
    for p in pieces:
        m = SECTION.fullmatch(p)
        if m:
            cur = m.group(1)
            continue
        if cur is None or not cur.endswith(".c"):
            continue
        pending_line = None
        for tm in TOKEN.finditer(p):
            if tm.group(1):
                pending_line = int(tm.group(1))
            elif pending_line:
                tok = tm.group(2)
                if re.search(r"\d", tok) or tok.startswith(("BD-", "MISRA", "CERT", "METRIC")):
                    findings.append((cfg, cur, pending_line, tok))

# 3. Overlap
print(f"\nfindings parsed: {len(findings)}")
for cfg in sorted({f[0] for f in findings}):
    cfg_f = [f for f in findings if f[0] == cfg]
    hit = [f for f in cfg_f if any(
        f[2] in fix_lines.get(p, set()) or f[2] - 1 in fix_lines.get(p, set())
        for p in fix_lines if p.endswith(f[1].lstrip("/")) or f[1].lstrip("/").endswith(p)
    )]
    rules = defaultdict(int)
    for f in hit:
        rules[f[3]] += 1
    print(f"[{cfg}] line-level hits: {len(hit)}/{len(cfg_f)} findings on fixed lines: {dict(rules)}")
    for f in hit:
        print("   ", f[1].lstrip("/").replace("libexpat/", ""), f[2], f[3])
