# SWE-sweep C/C++ x Parasoft C++test experiment

Benchmark study: on the six C/C++ repositories of SWE-sweep
(https://swesweep.com/, facebookresearch/swe-sweep), how many of the
reference bugs can Parasoft C++test static analysis detect, compared with
published LLM-agent results?

Repos (reference bug counts): libexpat (9), jerryscript (15), hdf5 (14),
proj (21), z3 (11), tarantool (40).

## Method

1. Clone each repo at the SWE-sweep maxbug base ref and record the build with
   `compile_commands.json` (cmake, Unix Makefiles generator; ninja breaks
   cpptesttrace).
2. Convert the compile database to a Parasoft build data file with `cc2bdf.py`
   (project root = source root so all files are in scope).
3. Run `cpptestcli` (C++test Professional 2025.2.0, network license) with
   builtin configs: Recommended Rules, MISRA C 2025, MISRA C++ 2023,
   Flow Analysis Standard, Flow Analysis Aggressive. Each config runs in an
   isolated `-data` workspace to prevent cross-run result accumulation.
4. Parse the dev reports with `parse_findings.py` (per-file violation counts,
   rule breakdowns) and map findings onto each bug's `target_files` from
   `tests/swesweep_eval.json` in the swe-sweep task definitions.
5. Line-level ground truth (`line_check.py`, `line_check_jerry.py`): extract
   the base-side lines changed by real upstream fix commits after the base
   ref, then check whether any finding lands on those lines, against a
   random-co-location baseline.

## Key results so far

- File-level "coverage" of reference-bug files saturates (it tracks finding
  density, not detection).
- Line-level: hit rates are at or below the random baseline in every config
  (libexpat: FA Aggressive 3/279, MISRA ~2.5% vs ~4% baseline; jerryscript:
  FA Aggressive 16.7% vs 18.7% baseline). Exception: 3 `BD-PB-PTRSUB-2`
  findings in libexpat land exactly on lines modified by the CVE-2021-45960 /
  CVE-2022-23852 integer-overflow fixes.
- Published LLM-agent best on these same repos fixes 0-3 of the bugs with
  hidden-test verification.

## Files

- `run_cpptest.sh` - full pipeline for one repo (clone, configure, build, scan)
- `analyze.sh`, `analyze2.sh` - scan existing bdf with config groups
- `cc2bdf.py` - compile_commands.json to Parasoft .bdf converter
- `parse_findings.py` - dev-report parser (per-file counts + rule breakdowns)
- `line_check.py`, `line_check_jerry.py` - line-level overlap studies
- `bin/sqlite3` shim lives at `~/bin/sqlite3` (Python stdlib; unblocks PROJ build)
