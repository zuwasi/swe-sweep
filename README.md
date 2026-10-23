# SWE-sweep Workspace

Everything ESL produced around Meta Superintelligence Labs' [SWE-sweep](https://swesweep.com/) benchmark, in one repository. Public-facing pages (slide deck, article, LinkedIn posts) live separately in the [Public-html-pages](https://github.com/zuwasi/Public-html-pages) repository and are intentionally not duplicated here.

## Layout

| Folder | What it is |
|---|---|
| `mini-swe-sweep/` | The benchmark harness and all evidence: identical treatment for Amp and Claude Code, official SWE-sweep Docker verifiers as referee |
| `swe-cpptest/` | The Parasoft C++test control study: can classic static analysis find the SWE-sweep C/C++ bugs at all |

## mini-swe-sweep

Harness, drivers and evidence for the agent benchmark runs (October 18 to 21, 2026).

- `run_agent.sh`, `eval.sh`, `prompt.md` — the identical loop both agents ran: one-hour cap, patch capture, replay into the official SWE-sweep task images
- `drive_run2*.sh`, `run_at_*.sh`, `start_when_ready.sh` — run-2 orchestration (12 repos x 2 agents x 5 frozen bugs)
- `tasks/` — the 12 frozen SWE-sweep task definitions used (60 scored bugs)
- `patches/` — every accepted patch from run 2; `patches-runcosttier/` — archived run 1
- `results/` — run 2 verifier outputs (reward JSONs, job logs); `results-runcosttier/` — run 1
- `logs/`, `logs-runcosttier/` — agent session logs
- `results-run2-summary.txt`, `MINI-SWEEP-RESULTS.md` — headline: **Amp 4/60 (6.7%) vs Claude Code 2/60 (3.3%), same model (claude-opus-5-5) on both arms**
- `monitor/` — the live status monitor (`gen_status.py`, `status.html`) and the generator for the public results page (`gen_public.py`, published at zuwasi.github.io/Public-html-pages/mini-swe-sweep/)

Note: the heavy per-repo working clones (`repos/`, about 15 GB, re-creatable by re-cloning the target repositories) are not tracked here. The fast WSL working tree for re-running agents lives at `/home/danie/mini-swe-sweep`.

## swe-cpptest

Parasoft C++test Professional 2025.2.0 control study on 6 C/C++ SWE-sweep repos (libexpat, jerryscript, hdf5, proj, z3, tarantool), five configurations including MISRA C 2025 and MISRA C++ 2023 with aggressive flow analysis.

- `run_cpptest.sh`, `analyze.sh`, `analyze2.sh` — scan orchestration
- `parse_findings.py`, `cc2bdf.py`, `line_check*.py` — finding parsers and line-level ground-truth checks against the SWE-sweep oracle patches
- `*.out` — finding dumps per repo and config
- `RESULTS.md` — headline: **0 to 0.3% line-level overlap with the real bugs across ~500,000 findings**; static analysis is complementary, not a substitute

Note: the repo clones and C++test scan data modules used during the study (~128 GB under `hdf5/`, `jerryscript/`, `libexpat/`, `proj/`, `tarantool/`, `z3/`) are not tracked here.

## Related repositories

- Benchmark upstream: https://github.com/facebookresearch/swe-sweep
- Harness repo (this `mini-swe-sweep/` content is mirrored there): https://github.com/zuwasi/mini-swe-sweep
- Parasoft study (mirrored there): https://github.com/zuwasi/swe-sweep-parasoft-cpptest
- Public presentation, article and LinkedIn page: https://zuwasi.github.io/Public-html-pages/swe-sweep-harness-king/
