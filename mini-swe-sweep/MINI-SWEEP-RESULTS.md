# mini-swe_sweep: Claude Code vs Amp (low mode), 20 bugs, 4 languages

Date: 2026-10-18. Machine: AI-logic-lab (WSL2, Ubuntu 24.04, 24 cores).
Harness: `/home/danie/mini-swe-sweep/` (run_agent.sh, eval.sh, prompt.md).

## Design

- 20 SWE-sweep reference bugs, 5 per language, pass@1, no hints:
  - C/C++: libexpat (bugs 0c5dbd0bb0a5, 30d93b149d3d, 44558a21f1b7, 4e25524fb119, 69f40cffb664)
  - C#: roslyn (13e38774dd0d, 19392d53f4a9, 2068fcc3b53f, 21d406d9d4b2, 2730ba811675)
  - Java: gson (797489de243a, 89ed2dfbe1b3, b22995c188d0, f14521f7bdc3, f9267b01483c)
  - Python: click (0099eb6f2003, 4f1302f13075, 6017fe42f482, 679517d3ee49, 747fcbb3e083)
- One agent session per repo per agent (8 sessions total), identical SWE-sweep
  bug-hunting prompt (`prompt.md`), 1 hour cap per session.
- Claude Code: `claude -p --dangerously-skip-permissions` (default model, claude.ai login).
- Amp: `amp -m low -x` (low mode, Amp account).
- Scoring: official Harbor verifier in Docker (`sweep eval`), hidden tests per subtask,
  regression gate on the pre-existing suite. Network policy relaxed to "public" in local
  task copies (WSL kernel lacks CONFIG_NFT_FIB_INET; the agent phase was already complete,
  so this cannot affect result validity).

## Results

| Repo (lang) | Amp low | Claude Code |
|---|---|---|
| libexpat (C/C++) | **2/5** | 1/5 |
| click (Python) | 0/5 | **2/5** |
| gson (Java) | 0/5 | 0/5 |
| roslyn (C#) | 0/5 | 0/5 (22 regressions, zeroed by the gate) |
| **Total** | **2/20 (10%)** | **3/20 (15%)** |

All 8 sessions: agent patch applied, agent build OK, grader OK. No regressions except
Claude Code on roslyn (its 282-line diff broke pre-existing tests, score 0 by the gate).

Session durations: Amp 11-13 min on libexpat/click/gson, 60 min (cap) on roslyn.
Claude Code 4-25 min on libexpat/click/gson, 60 min (cap) on roslyn.

## Observations

1. Both agents resolved bugs that direct LLMs with the same budget largely miss, and the
   two arms resolved *different* bugs (libexpat: Amp 2, Claude 1; click: Amp 0, Claude 2).
   Harness diversity is real: neither dominates.
2. Both scored 0 on gson and roslyn. roslyn's scale and 1 h cap defeated both; the SWE-sweep
   paper gives agents 12 h and 1,000 steps.
3. 10-15% resolution in a 1 h pass@1 pilot is in line with the published direct-LLM
   baselines (0-20%) despite our much tighter time budget, supporting the agent-vs-LLM
   hypothesis, though 20 bugs is too small for significance.

## Caveats

- n=20; differences of 1-2 bugs are noise. This is a calibration run, not a conclusion.
- Claude Code used its default model/mode; Amp used low mode (GLM-class routing). The arms
  are effort- and cost-tier comparable, not same-model. A same-model pass is the natural
  follow-up.
- roslyn ran under a 1 h cap; results there say more about the cap than about the agents.

## Reproduce

```
CAP_SECONDS=3600 ./run_agent.sh amp libexpat      # or claude
./eval.sh libexpat amp                            # needs docker group
cat results/jobs-*/<ts>/swe-sweep__*/verifier/reward.json
```

---

# Run 2 final results: same model on both arms (claude-opus-5-5), 12 repos, 60 bugs

Completed 2026-10-21 17:07 IDT. Arms: Amp (default mode) vs Claude Code (headless
defaults), identical prompt, identical frozen repos, 1-hour cap per agent-repo session,
official SWE-sweep Docker verifiers as the only referee.

| Repo | Lang | Amp | Claude Code |
|---|---|---|---|
| libexpat | C | 0/5 | 0/5 |
| click | Python | **1/5** | 0/5 |
| gson | Java | **1/5** | 0/5 |
| roslyn | C# | 0/5 (1 regression, zeroed by the gate) | 0/5 |
| z3 | C++ | 0/5 (399-line patch, cap expired) | 0/5 (1,006 diff lines) |
| tokio | Rust | 0/5 | **1/5** |
| hdf5 | C | 0/5 | 0/5 |
| proj | C++ | **1/5** | 0/5 |
| black | Python | 0/5 | 0/5 |
| rxjava | Java | **1/5** | **1/5** |
| fsharp | C# | 0/5 | 0/5 |
| syn | Rust | 0/5 | 0/5 |
| **Total** | | **4/60 (6.7%)** | **2/60 (3.3%)** |

Notes:
- Three Claude Code sessions (black, proj, rxjava batch-3 rerun) ended at the Claude
  plan spend cap (exit=1). The patches they had produced were fully evaluated by the
  SWE-sweep verifier and are scored; rxjava resolved 1/5 cleanly, the other two 0/5.
- Placement vs the official leaderboard (full 100-repo runs, Sep 24, 2026): best entry
  GPT-5.6 Sol / mini-SWE-agent at 4.7% ($7,230); Opus 5 (xhigh) / mini-SWE-agent at
  1.3%. Our Amp subsample result (6.7%) is above the SOTA entry; n=60 makes 4-vs-2
  directional, not statistically conclusive.
- Run 1 (cost tier, not model-equal): Amp low 2/20 vs Claude Code 3/20; Claude roslyn
  zeroed by 22 regressions.

Public page: https://zuwasi.github.io/Public-html-pages/mini-swe-sweep/
Deck: https://zuwasi.github.io/Public-html-pages/swe-sweep-harness-king/
