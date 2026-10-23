#!/usr/bin/env python3
"""Parse Parasoft dev-report HTML files into per-file finding counts.

Usage: parse_findings.py <task_name> [repo_root]
Dev-report sections start with a file path between pipes; each violation in a
section ends with its rule id either bare (BD-PB-NOTINIT-1) or parenthesized
(METRIC.CC-3).
"""
import glob
import html
import json
import re
import sys

task = sys.argv[1]
root = f"/home/danie/swe-cpptest/{task}"
repo = sys.argv[2] if len(sys.argv) > 2 else f"/home/danie/swe-cpptest/{task}"

evals = glob.glob(f"/mnt/c/Users/danie/amp-demos/swe-sweep/tasks/swe-sweep__{task}/tests/swesweep_eval.json")
subtasks = json.load(open(evals[0]))["subtasks"] if evals else []

SECTION = re.compile(r"\|(/?[\w.+-]+(?:/[\w.+-]+)*\.(?:c|cc|cpp|h|hpp|cxx))\|")
RULE = re.compile(r"\|\(?([A-Za-z][A-Za-z0-9]*(?:[._-][A-Za-z0-9]+)+)\)?\|")

def is_rule(tok):
    return bool(re.search(r"\d", tok)) or tok.startswith(("BD-", "MISRA", "CERT", "METRIC", "AUTOSAR", "HIS", "PB-", "SEC"))

def parse_dev_report(path):
    h = open(path, encoding="utf-8", errors="replace").read()
    txt = re.sub(r"<[^>]+>", "|", h)
    txt = html.unescape(txt)
    txt = re.sub(r"\|+", "|", txt)
    counts, rules = {}, {}
    cur = None
    pieces = re.split(r"(\|/?[\w.+-]+(?:/[\w.+-]+)*\.(?:c|cc|cpp|h|hpp|cxx)\|)", txt)
    for p in pieces:
        m = SECTION.fullmatch(p)
        if m:
            cur = m.group(1)
            counts.setdefault(cur, 0)
            rules.setdefault(cur, {})
        elif cur:
            for rm in RULE.finditer("|" + p + "|"):
                r = rm.group(1)
                # skip non-rule tokens that appear in prose
                if is_rule(r):
                    counts[cur] += 1
                    rules[cur][r] = rules[cur].get(r, 0) + 1
    return counts, rules

for cfg_dir in sorted(glob.glob(f"{root}/report-*")):
    reps = glob.glob(f"{cfg_dir}/report*_dev1.html")
    if not reps:
        continue
    rep = max(reps, key=lambda p: __import__("os").path.getmtime(p))
    cfg = cfg_dir.split("/report-")[1].split("/")[0]
    counts, rules = parse_dev_report(rep)
    print(f"== {task} [{cfg}] ==  {sum(counts.values())} findings in {len(counts)} files")
    for f, n in sorted(counts.items(), key=lambda kv: -kv[1])[:12]:
        short = f.replace(repo, "").lstrip("/").replace("libexpat/", "")
        print(f"  {n:4d}  {short}  {dict(sorted(rules[f].items(), key=lambda kv: -kv[1]))}")
    hit = sum(
        1 for s in subtasks
        if any(any(f.endswith(t) for f in counts) for t in s.get("target_files", []))
    )
    print(f"  file-level reference-bug coverage: {hit}/{len(subtasks)}\n")
