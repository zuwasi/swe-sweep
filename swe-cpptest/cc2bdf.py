#!/usr/bin/env python3
"""Convert a GCC compile_commands.json into a Parasoft build data file (.bdf).

Usage: cc2bdf.py <compile_commands.json> <project_name> <out.bdf> [source_root]

Each bdf entry records the compiler and every command-line argument, with
working_dir set to source_root (the project root) so all source files fall
inside the imported project's scope.
"""
import json
import shlex
import sys

cc_path, project_name, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
source_root = sys.argv[4] if len(sys.argv) > 4 else None

with open(cc_path) as f:
    entries = json.load(f)

seen = set()
with open(out_path, "w") as out:
    for e in entries:
        cmd = e.get("command") or " ".join(e.get("arguments", []))
        tokens = shlex.split(cmd)
        if not tokens:
            continue
        src = e.get("file", "")
        key = (tokens[0], src)
        if key in seen:  # one entry per (compiler, source file)
            continue
        seen.add(key)
        wd = source_root or e.get("directory", ".")
        out.write("------- cpptestscan v.10.7.3 (cc2bdf) -------\n")
        out.write(f"working_dir={wd}\n")
        out.write(f"project_name={project_name}\n")
        for t in tokens:
            out.write(f"arg={t}\n")

print(f"wrote {len(seen)} entries to {out_path}")
