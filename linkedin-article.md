# The Harness Is the King: We Ran Amp and Claude Code on Meta's SWE-sweep. The Agent Framework Decided the Outcome.

**By Daniel Liezrowice, CTO, ESL - Engineering Software Lab**

We ran two commercial coding agents on Meta Superintelligence Labs' hardest bug benchmark, held the model identical on both sides, and changed only the harness around it. The result: 4/60 reference bugs resolved versus 2/60. Same weights. Same prompt discipline. Same referee. The harness doubled the outcome.

This article explains what we did, what the agents got right and wrong, why we also ran Parasoft C++test as a control, and why we believe the harness, not the model, is what you should be evaluating and buying.

---

## Table of Contents

1. [What SWE-sweep is](#1-what-swe-sweep-is)
2. [What the benchmark's own authors say about harnesses](#2-what-the-benchmarks-own-authors-say-about-harnesses)
3. [The academic context: the harness debate](#3-the-academic-context-the-harness-debate)
4. [Our experiment: hold the model, vary the harness](#4-our-experiment-hold-the-model-vary-the-harness)
5. [The result: Amp 4/60, Claude Code 2/60](#5-the-result-amp-460-claude-code-260)
6. [The bugs, up close: what the agents fixed and what they failed](#6-the-bugs-up-close-what-the-agents-fixed-and-what-they-failed)
7. [Before this: the quantum-compiler study said the same thing](#7-before-this-the-quantum-compiler-study-said-the-same-thing)
8. [The Parasoft C++test control: 0 to 0.3%](#8-the-parasoft-cptest-control-0-to-03)
9. [Why the harness is the king](#9-why-the-harness-is-the-king)
10. [Honest limitations](#10-honest-limitations)
11. [What to do Monday](#11-what-to-do-monday)
12. [Links and full transparency](#12-links-and-full-transparency)

The companion slide deck (24 slides, every diff and verifier output shown): [The Harness Is the King, presentation](https://zuwasi.github.io/Public-html-pages/swe-sweep-harness-king/index.html)

---

## 1. What SWE-sweep is

[SWE-sweep](https://swesweep.com/) is a benchmark from Meta Superintelligence Labs (Lieret, Ma, Wei, Yang, Press and colleagues, ICLR 2026 preprint, [facebookresearch/swe-sweep](https://github.com/facebookresearch/swe-sweep)). It asks a harder question than SWE-bench. Not "fix this reported issue", but:

> An agent is given a real repository that contains an unknown number of confirmed bugs and no hints. How many can it find and fix?

Three properties make it brutal:

- **100 real repositories, 4,100 confirmed bugs.** Each snapshot is a commit where the maximum number of upstream-confirmed bugs coexist.
- **No hints.** No issue text, no filenames, no line ranges. The agent must explore, hypothesize and repair on its own.
- **Unforgiving scoring.** Every candidate fix must pass hidden fail-to-pass tests from the upstream pull request, plus the repository's entire existing test suite. One regression zeroes the whole repo's reward.

The official leaderboard is sobering. The best entry in the world (GPT-5.6 Sol on the minimal mini-SWE-agent scaffold) resolves **4.7%** of the bugs for **$7,230** per full run. Most entries sit between 0.1% and 2.5%.

> **[INSERT IMAGE 1 here]**
> **Suggested headline: "The official SWE-sweep leaderboard: the best entry in the world resolves 4.7% for $7,230"**
> Image file: `C:\Users\danie\Public-html-pages\swe-sweep-harness-king\assets\swesweep-leaderboard-crop.png`

---

## 2. What the benchmark's own authors say about harnesses

The SWE-sweep FAQ directly addresses whether the agent scaffold matters:

> "Our paper has an ablation with Claude Code and Codex. Neither seems to significantly outperform mini-swe-agent (to the contrary, mini-swe-agent is even quite a bit better than Codex)."
> (SWE-sweep FAQ, [swesweep.com](https://swesweep.com/), accessed October 21, 2026)

The benchmark's own authors found that harness choice does not separate the big scaffolds at their resolution. That is exactly the question we set out to test at ESL, but head to head, same model, production harnesses, with the SWE-sweep verifier as the only referee.

---

## 3. The academic context: the harness debate

The 2026 research conversation consistently says the loop around the model carries much of the outcome:

- **SWE-agent's Agent-Computer Interface ablation** (NeurIPS 2024, [arXiv:2409.12177](https://arxiv.org/abs/2409.12177)): resolution moved from 3.8% to 12.5% with no new model weights.
- **Code as Agent Harness: A Survey** ([arXiv:2605.18747](https://arxiv.org/abs/2605.18747), UIUC, Meta and Stanford, 2026): "The bottleneck of autonomy is not only the reasoning ability of the base model, but also the reliability of the system that connects model outputs to long-horizon actions and persistent states."
- **Kaggle's 2026 SDLC analysis**: roughly 90% of an agent's engineering is the harness, 10% the model.

> **[INSERT IMAGE 2 here]**
> **Suggested headline: "The research conversation in 2026: the harness, not the weights, is the variable that moves"**
> Image file: `C:\Users\danie\amp-demos\link_s6_live.png` (slide 6 of the deck)

---

## 4. Our experiment: hold the model, vary the harness

We built a small harness, **mini-swe-sweep**, that gives both agents identical treatment. Everything is public and reconstructable: [github.com/zuwasi/swe-sweep](https://github.com/zuwasi/swe-sweep) and [github.com/zuwasi/mini-swe-sweep](https://github.com/zuwasi/mini-swe-sweep).

The core loop is deliberately boring:

```
# run_agent.sh (core): identical loop for both CLIs
cd "$REPO" && timeout 3600 "$AGENT_CLI" < prompt.md > session.log
git diff > "patches/${AGENT}__${REPO}.diff"

# eval.sh: replay into the official SWE-sweep task image
run_verifier "$TASK_DIR" --patch "patches/${AGENT}__${REPO}.diff"
```

- **Two arms, one model:** Amp (default mode) and Claude Code (headless defaults), both running `claude-opus-5-5`. The harness is the only variable.
- **12 repositories** spanning C, C++, C#, F#, Java, Python and Rust: libexpat, click, gson, roslyn, z3, tokio, hdf5, proj, black, rxjava, fsharp, syn.
- **5 frozen reference bugs per repo** (60 scored tasks), a 60-minute cap per session, and the official SWE-sweep Docker verifiers as the only referee. The agents never see the tests. Cheating is impossible by construction.

---

## 5. The result: Amp 4/60, Claude Code 2/60

| Entry | Model | Agent | Score | Cost |
|---|---|---|---|---|
| **ESL benchmark** | claude-opus-5-5 | **Amp (default)** | **4/60 = 6.7%** | est. $28-48 |
| Official rank 1 | GPT-5.6 Sol (xhigh) | mini-SWE-agent | 4.7% | $7,230 |
| **ESL benchmark** | claude-opus-5-5 | **Claude Code (headless)** | **2/60 = 3.3%** | est. $13-24 |
| Official rank 5 | Opus 5 (xhigh) | mini-SWE-agent | 1.3% | $5,363 |

Amp resolved bugs in 4 of 12 repos (click, gson, proj, rxjava). Claude Code in 2 (tokio, rxjava). Amp finished all 12 sessions inside the one-hour cap. Three Claude Code sessions ended when the tool hit its own plan spend limit; the patches those sessions produced were still graded by the real verifier.

One resolved bug is worth 1.67 points on a 60-bug subsample, so 4-vs-2 is directional evidence, not statistical proof. But it points the same way as everything else we have measured.

> **[INSERT IMAGE 3 here]**
> **Suggested headline: "The final scoreboard: same model on both arms, 4/60 vs 2/60"**
> Image file: `C:\Users\danie\amp-demos\link_s9c.png` (slide 9 of the deck)

---

## 6. The bugs, up close: what the agents fixed and what they failed

### What Amp got right: click (Python)

Two Python 3 API bugs in bundled examples: a config example writing bytes to a file opened for text, and a call to a removed private helper replaced by the public stream API.

```
-        with open(filename, "wb") as file:
+        with open(filename, "w") as file:      # configparser.write needs text mode

-                img = Image.open(click.get_binary_stdin())
+                img = Image.open(click.get_binary_stream("stdin"))
```

Small, surgical, exactly at the failing lines. Hidden tests passed, original suite stayed green. This is the discipline pattern we saw across all four Amp wins: locate, minimally fix, stop.

### What Claude Code got right: tokio (Rust)

Two latent bugs in one patch: the macro's requires-argument list was missing `crate`, and `size_hint` could overflow on huge stream maps (fixed with `saturating_add`). 553 diff lines total, scored 1/5 with a clean regression gate. A real, minimal, correct fix.

### What both failed: z3 (C++) and the regression gate

- **z3 (C++):** Amp produced a 399-line patch that looked plausible and scored 0. Big exploratory diffs without a verified failing test are how agents lose on this benchmark.
- **roslyn (C#):** a plausible fix was zeroed by a single broken existing test. The regression gate does the judging, not the reviewer's eye.

> **[INSERT IMAGE 4 here]**
> **Suggested headline: "Claude Code's tokio fix: two latent bugs in one patch, judged by hidden tests"**
> Image file: `C:\Users\danie\amp-demos\final_s12_live2.png` (slide 12 of the deck)

---

## 7. Before this: the quantum-compiler study said the same thing

This was not our first controlled comparison. In an earlier ESL study on quantum-compiler kernel generation ([The Harness Beats the Model](https://zuwasi.github.io/Public-html-pages/harness-beats-model.html)), Amp solved 4/4 kernels for **$1.93** while Claude Code at maximum effort stopped at 3/4 for **$75.40**: 39x cheaper and 24x faster per iteration. Different benchmark, different model class, same conclusion: the loop around the model decides.

---

## 8. The Parasoft C++test control: 0 to 0.3%

Before crediting agents, we asked: can classic static analysis find these bugs at all? We ran licensed **Parasoft C++test Professional 2025.2.0** on six C/C++ SWE-sweep repos (libexpat, jerryscript, hdf5, proj, z3, tarantool) in five configurations: Recommended Rules, Flow Analysis Standard, Flow Analysis Aggressive, MISRA C 2025 and MISRA C++ 2023.

About **500,000 findings** in total. Ground truth: a finding "hits" a bug only if its line falls on a base-side line the upstream fix actually changed.

**Result: 0 to 0.3% line-level overlap**, and wherever we could compute a fair baseline, the hit rate sat at or below the random density of changed lines. Full method and per-config data: [github.com/zuwasi/swe-sweep-parasoft-cpptest](https://github.com/zuwasi/swe-sweep-parasoft-cpptest).

This is not a knock on C++test. SWE-sweep scores behavioral regressions: a null re-entry in an RxJava operator, a swapped hash-function name in a C# compiler backend, an overflow in a Rust `size_hint`. Each needs semantics, intent, and a failing test to reason from. Static analysis checks patterns and invariants reachable from syntax and dataflow; no rule in 500,000 findings describes the contract that the hidden tests judge.

For ESL's home turf (MISRA, CERT, AUTOSAR, safety-critical work), C++test is exactly the right tool and we deploy it daily. The pipeline we recommend to clients: **static analysis for the rule book, agents for behavioral bugs, hidden tests as the referee.**

---

## 9. Why the harness is the king

The model is the engine. The harness is the car. Nobody commutes to work on an engine.

In our SWE-sweep runs, the deciding harness behaviors were: repo-wide context management, knowing when to stop exploring and start editing, patch-size discipline, and running the visible test suite before declaring victory. The same engine scored 1.3%, 3.3% or 6.7% depending on the loop you put around it.

That is why we say the harness is the product, and on this benchmark, **Amp built a better one.** Twice measured, twice ahead, at dramatically lower cost. Full analysis in [The Harness Is the Product](https://zuwasi.github.io/Public-html-pages/harness-is-the-product/).

> **[INSERT IMAGE 5 here]**
> **Suggested headline: "The winner: Amp. Two studies, same direction, 39x cheaper"**
> Image file: `C:\Users\danie\Public-html-pages\swe-sweep-harness-king\assets\esl-logo.png` or a deck slide you like

---

## 10. Honest limitations

- **n = 60, one seed.** Directional evidence, not statistical proof.
- **Subsample:** 5 frozen bugs per repo, not the full 4,100. Our percentages are placements, not record claims.
- **Quota endings:** three Claude Code sessions ended at the plan spend cap. Their patches were still graded by the real verifier, but those sessions had less effective exploration time.
- **Costs are estimates** from measured wall time, not vendor invoices.
- **Both harnesses are good.** Claude Code resolved bugs Amp missed (tokio). This is a ranking on one benchmark slice, not a verdict for all workloads.

---

## 11. What to do Monday

1. Stop shopping for the biggest model. Evaluate harnesses on your own repos: context management, tool execution, verify loops, spend discipline, regression fences.
2. Keep static analysis for the rule book and compliance. Keep agents for behavioral bugs. Keep hidden tests as the only referee.
3. Budget the plan limit, not just the tokens. Quota interruptions cost us five Claude batch attempts before we stabilized the protocol.
4. Run candidates on your own code. The leaderboard is a place to start, not a decision.

---

## 12. Links and full transparency

Everything is public and reconstructable, including the frozen task definitions, every patch, and the raw verifier outputs:

- **Full transparency workspace (this benchmark's repo):** [github.com/zuwasi/swe-sweep](https://github.com/zuwasi/swe-sweep)
- **Harness repo with all runs:** [github.com/zuwasi/mini-swe-sweep](https://github.com/zuwasi/mini-swe-sweep)
- **Public per-run results page:** [zuwasi.github.io/Public-html-pages/mini-swe-sweep/](https://zuwasi.github.io/Public-html-pages/mini-swe-sweep/)
- **Parasoft control study:** [github.com/zuwasi/swe-sweep-parasoft-cpptest](https://github.com/zuwasi/swe-sweep-parasoft-cpptest)
- **The 24-slide presentation:** [zuwasi.github.io/Public-html-pages/swe-sweep-harness-king/](https://zuwasi.github.io/Public-html-pages/swe-sweep-harness-king/index.html)
- **The benchmark:** [swesweep.com](https://swesweep.com/) and [facebookresearch/swe-sweep](https://github.com/facebookresearch/swe-sweep)
- **Prior ESL study:** [The Harness Beats the Model](https://zuwasi.github.io/Public-html-pages/harness-beats-model.html)

*All runs executed and verified between October 18 and 21, 2026. Every number links to logged runs, real patches and Docker verifier outputs.*

---

*Daniel Liezrowice is CTO of ESL - Engineering Software Lab, an embedded software consultancy and Parasoft and Perforce partner in Israel for over 20 years. ESL benchmarks AI agents with the same evidence discipline used for safety-critical code: [eswlab.com](https://eswlab.com/) | [linkedin.com/in/liezrowice](https://www.linkedin.com/in/liezrowice/)*
