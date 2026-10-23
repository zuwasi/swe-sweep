# Parasoft C++test vs SWE-sweep Reference Bugs: Six-Repo Pilot

Parasoft C++test Professional 2025.2.0, five configurations, six C/C++ SWE-sweep repos.
Question: does static analysis find the reference behavioral bugs that SWE-sweep scores?
If yes, agents are unnecessary. If it covers other areas, they may be complementary.

## Configurations

1. Recommended Rules (built-in)
2. Flow Analysis Standard
3. Flow Analysis Aggressive
4. MISRA C 2025 (builtin://MISRA C 2025)
5. MISRA C++ 2023

## Violations found

| Repo | Recommended | FA Standard | FA Aggressive | MISRA C 2025 | MISRA C++ 2023 |
|---|---|---|---|---|---|
| libexpat | 68 | 74 | 297 | 14,296 | 13,219 |
| jerryscript | 333 | 297 | 446 | 20,815 | 15,023 |
| hdf5 | 2,154 | 2,748 | 3,353 | 59,628 | 39,936 |
| proj | 1,097 | 1,118 | 1,232 | 36,874 | 38,010 |
| z3 | 3,315 | 2,490 | 2,986 | 41,704 | 54,465 |
| tarantool | 1,239 | 2,305 | 3,570 | 79,364 | 60,154 |
| **total** | **8,206** | **9,032** | **11,884** | **252,683** | **220,807** |

Roughly half a million findings across five configs. Recommended Rules and both Flow
Analysis modes flag nearly the same files, so their coverage adds little to each other.

## File-level reference-bug coverage

Files containing a reference bug that received at least one finding:

| Repo | Ref bugs | Recommended | FA Std | FA Aggr | MISRA C 2025 | MISRA C++ 2023 |
|---|---|---|---|---|---|---|
| libexpat | 9 | 9/9 | 9/9 | 9/9 | 9/9 | 9/9 |
| jerryscript | 15 | 12/15 | 12/15 | 12/15 | 15/15 | 14/15 |
| hdf5 | 14 | 13/14 | 14/14 | 14/14 | 14/14 | 14/14 |
| proj | 21 | 19/21 | 20/21 | 21/21 | 21/21 | 19/21 |
| z3 | 11 | 0/11 | 7/11 | 7/11 | 11/11 | 11/11 |
| tarantool | 40 | 26/40 | 29/40 | 30/40 | 35/40 | 35/40 |

MISRA covers the most files because it flags almost every file (1,853 of ~2,022 for z3).
File-level coverage is a weak signal; line-level is the decisive metric.

## Line-level overlap with ground-truth fixes

Findings whose line falls on a base-side line changed by the upstream fix
(generated from the SWE-sweep oracle patches; scripts: `line_check.py`,
`line_check_jerry.py`, `line_check_z3.py`, `line_check_tarantool.py`).

| Repo | Fixed lines | Recommended | FA Std | FA Aggr | MISRA C 2025 | MISRA C++ 2023 |
|---|---|---|---|---|---|---|
| libexpat | 279 (3 CVE fixes) | 0 | 0 | 3/279 (1.1%) | ~2.5% (baseline ~4%) | ~2.5% |
| jerryscript | density 18.7% | - | 14.2% | 16.7% | 11.4% | - |
| z3 | 248 | 3/3,315 (0.1%) | 2/2,489 (0.1%) | 2/2,985 (0.1%) | 20/41,704 (0.05%) | 18/54,465 (0.03%) |
| tarantool | 1,339 | 2/1,239 (0.2%) | 6/2,103 (0.3%) | 6/3,357 (0.2%) | 213/79,131 (0.27%) | 193/59,989 (0.32%) |

Genuine detections (FA Aggressive, z3 and tarantool combined): 2 hits on actual fix
lines (`BD-PB-CC-2` complexity findings that coincide with changed regions, plus
`BD-PB-CHECKRET-2`/`BD-PB-VOVR-3` in tarantool). libexpat's 3 hits are
`BD-PB-PTRSUB-2` on lines modified by the CVE-2021-45960 / CVE-2022-23852 overflow
fixes, which is real detection of the vulnerable pattern.

Everywhere else the hit rate sits at or below the random baseline (fraction of scanned
lines that the fixes touched). The MISRA "hits" are style-rule violations
(`RULE_15_6`, `RULE_5_10`, `RULE_10_3`...) that happen to fall inside changed hunks;
they carry no signal about the behavioral bug.

## Comparison with published LLM baseline (direct LLM, no agent)

| Repo | Best direct-LLM resolution rate |
|---|---|
| libexpat | 11.1% |
| jerryscript | 20.0% |
| hdf5 | 0% |
| proj | 9.5% |
| z3 | 0% |
| tarantool | 7.5% |

## Conclusion

1. C++test, in any of the five configurations, does not detect the SWE-sweep
   reference behavioral bugs beyond chance. Flow Analysis Aggressive found the
   libexpat CVE pattern and a couple of coincidental hits; MISRA contributes zero
   signal on these bugs while adding 100k-250k findings of triage burden.
2. The tools answer different questions. C++test is strong for coding-standard
   compliance (MISRA) and well-defined defect patterns (leaks, overflow, unchecked
   returns). The reference bugs are behavioral regressions that only the hidden
   tests observe.
3. Therefore the agent experiment (Amp low vs Claude Code, same model, SWE-sweep
   C/C++ repos) is not replaced by C++test; it is complementary. Run both:
   C++test as the static-analysis gate, agents as the bug-fixing arm.
