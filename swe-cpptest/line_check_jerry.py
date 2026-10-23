#!/usr/bin/env python3
"""Line-level overlap study for jerryscript v2.2.0: do C++test findings fall on
lines that upstream later fixed? Approximates the 15 reference bugs with all
non-merge fix-looking commits in v2.2.0..v2.3.0 touching jerry-core/jerry-libm.
"""
import glob
import html
import os
import re
import subprocess
from collections import defaultdict

REPO = "/home/danie/swe-cpptest/jerryscript-full"
BASE = "v2.2.0"
END = "v2.3.0"

SKIP = re.compile(r"bump|sync|typo|style|readme|docs|license|copyright|ci|cmake|build", re.I)
FIX = re.compile(r"fix|leak|crash|overflow|correct|wrong|bug", re.I)


def sh(*args):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True).stdout


fix_lines = defaultdict(set)
used = []
for line in sh("git", "log", "--no-merges", "--format=%H %s", f"{BASE}..{END}",
               "--", "jerry-core", "jerry-libm").splitlines():
    h, subject = line.split(" ", 1)
    if SKIP.search(subject) or not FIX.search(subject):
        continue
    diff = sh("git", "diff", BASE, h, "--", "jerry-core", "jerry-libm")
    used.append(subject)
    old = cur = None
    for dl in diff.splitlines():
        if dl.startswith("--- a/"):
            old = dl[6:]
        elif dl.startswith("+++ b/"):
            cur = dl[6:]
        elif dl.startswith("@@") and old and cur:
            m = re.search(r"-(\d+)(?:,(\d+))?", dl)
            if m:
                start = int(m.group(1))
                n = int(m.group(2)) if m.group(2) is not None else 1
                for ln in range(start, start + max(n, 1)):
                    fix_lines[old].add(ln)

print(f"fix commits used: {len(used)}")
for s in used[:20]:
    print("  -", s[:80])

# Parse findings from all configs
ROOT = "/home/danie/swe-cpptest/jerryscript"
SECTION = re.compile(r"\|(/?[\w.+-]+(?:/[\w.+-]+)*\.(?:c|cc|cpp|h|hpp|cxx))\|")
TOKEN = re.compile(r"\|(\d+):[\s\xa0]*\||\|\(?([A-Za-z][A-Za-z0-9]*(?:[._-][A-Za-z0-9]+)+)\)?\|")

for cfg_dir in sorted(glob.glob(f"{ROOT}/report-*")):
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
    findings = []
    for p in pieces:
        m = SECTION.fullmatch(p)
        if m:
            cur = m.group(1)
            continue
        if cur is None or not cur.endswith(".c"):
            continue
        pl = None
        for tm in TOKEN.finditer(p):
            if tm.group(1):
                pl = int(tm.group(1))
            elif pl:
                tok = tm.group(2)
                if re.search(r"\d", tok) or tok.startswith(("BD-", "MISRA", "CERT", "METRIC")):
                    findings.append((cur, pl, tok))
    hits = []
    for f, ln, rule in findings:
        norm = f.lstrip("/")
        for pre, lns in fix_lines.items():
            if norm.endswith(pre) and (ln in lns or ln - 1 in lns or ln + 1 in lns):
                hits.append((f, ln, rule))
                break
    rules = defaultdict(int)
    for f, ln, r in hits:
        rules[r] += 1
    print(f"[{cfg}] findings: {len(findings)}, line-level hits: {len(hits)}  {dict(sorted(rules.items(), key=lambda kv: -kv[1])[:8])}")
    for f, ln, r in hits[:8]:
        print("   ", f.lstrip("/").replace("jerryscript/", ""), ln, r)
