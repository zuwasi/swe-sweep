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

## Reconstruct everything

Everything here is reproducible from public sources. No large artifacts are stored in this repository; the steps below pull them from their origins.

### 1. Rebuild the agent benchmark (mini-swe-sweep)

1. Clone the benchmark: `git clone https://github.com/facebookresearch/swe-sweep.git` and follow its setup (Docker images for the verifiers).
2. Clone the harness: `git clone https://github.com/zuwasi/mini-swe-sweep.git` (identical content to `mini-swe-sweep/` here).
3. The 12 frozen task definitions are in `mini-swe-sweep/tasks/` (60 scored bugs, 5 per repo, with hidden fail-to-pass tests and the verifier `test.sh`).
4. Point `run_agent.sh` at a repo and an agent CLI (`amp` or `claude`); it runs one prompt under a 60-minute wall-clock cap and captures the patch. `drive_run2*.sh` drive all 12 repos x 2 agents.
5. Grade with `eval.sh`, which replays each patch into the official SWE-sweep task image and writes `verifier/reward.json` (`n_resolved`, `n_regressions`). Raw verifier outputs are in `results/` (run 2) and `results-runcosttier/` (run 1).
6. Expected outcome: Amp 4/60 (6.7%), Claude Code 2/60 (3.3%), same model `claude-opus-5-5` on both arms.

The target repositories (click, gson, roslyn, z3, tokio, hdf5, proj, black, rxjava, fsharp, libexpat, syn) are public upstream repos; clone them at the base commits recorded in each task definition. They are not stored here.

### 2. Rebuild the Parasoft C++test control (swe-cpptest)

1. Install Parasoft C++test Professional 2025.2.0 (licensed product from parasoft.com; installers are not redistributable and are not stored here).
2. Clone the six study repos (libexpat, jerryscript, hdf5, proj, z3, tarantool) at the base commits in the task definitions.
3. Run `run_cpptest.sh` per repo with each of the five configurations: Recommended Rules, Flow Analysis Standard, Flow Analysis Aggressive, MISRA C 2025, MISRA C++ 2023.
4. Parse the reports with `parse_findings.py` / `cc2bdf.py`; the `*.out` files here are the parsed finding dumps.
5. Check line-level overlap with the reference bugs using `line_check*.py` against the SWE-sweep oracle patches. Expected outcome: 0 to 0.3% of findings land on lines the upstream fixes changed, at or below the random density of changed lines.

## Related repositories

- Benchmark upstream: https://github.com/facebookresearch/swe-sweep
- Harness repo (this `mini-swe-sweep/` content is mirrored there): https://github.com/zuwasi/mini-swe-sweep
- Parasoft study (mirrored there): https://github.com/zuwasi/swe-sweep-parasoft-cpptest
- Public presentation, article and LinkedIn page: https://zuwasi.github.io/Public-html-pages/swe-sweep-harness-king/

