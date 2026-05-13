# SESSION HANDOFF — Resume on PC

**Generated:** 2026-05-11 18:47 PDT (on Daniel's laptop)
**Resume by:** 2026-05-11 18:55 PDT (so agents have ~2 hours until 21:00 deadline)
**Project:** RL_project_185 — Semantic Failure Localization for PER (CS 285 Berkeley, team: Parshawn / Matei / Daniel)
**You are now running on:** Daniel's PC (Ubuntu 24.04, RTX 5070 Ti, agile-quadrupeds Modal workspace)

---

## TL;DR — what to do right now

1. **Verify environment (1 min)** — run the preflight checks in §3.
2. **Confirm with user the Modal secret exists** (or have them create it) — §3 explains.
3. **Fire all 6 agents in parallel** using the pre-baked prompts in §5.
4. **Synthesize results at 20:50 PDT** into `agent_reports/9pm_presentation.md` for Daniel to present to teammates at 21:00.

Do **not** re-do the audit, re-do the literature scan, or re-discuss thesis framings. Those are done. Skip to §3.

---

## 1. Why we're here (the 60-second story)

Daniel's teammate Parshawn built **Semantic PER**: VLM-guided failure localization that boosts replay priority around a VLM-identified failure timestep. 36 Modal runs already exist on W&B (project `RL_project`). Honest read of those results:

- **Oracle (privileged sim state) beats PER on average (0.417 vs 0.383)** — but it's not a real method, it needs `achieved_goal` from the simulator
- **GPT-4o VLM variant underperforms PER (0.306 vs 0.383)** — the novel mechanism is the weakest link
- **PER's average is almost entirely FetchPush (0.95)** — broken on Pick & Slide (~0.10 each)
- **HER is missing from the ablation** — it's THE standard baseline for Fetch envs; `her_buffer.py` exists but is untested
- **3 seeds with σ=0.1–0.4** — most differences are statistical noise
- **The "VLM beats Oracle on FetchSlide" headline was a bug story** — Oracle v1 used argmin-distance which finds the puck post-release

**The scoop concern:** arXiv 2602.01915 — "VLM-Guided Experience Replay" (Sharony, Mannor, et al., Technion+NVIDIA, Feb 2026) does almost exactly the high-level pitch: VLM scores trajectories, boosts replay, multiplicative with TD-error, tested on SAC+manipulation, beats PER. **They published 3 months ago.** Daniel did not know about this. Differentiating against it is critical.

**Two paths we're pursuing in parallel tonight:**

- **Path A** — *Causal Failure Localization as the Counter-Direction to Goal-Satisfaction Scoring.* Sharony boosts success-like transitions; we boost failure-causing transitions. Add HER baselines, refine the oracle, build a bidirectional variant that combines both directions.
- **Path C** — *Counterfactual VLM Reasoning for Credit Assignment.* Don't just ask the VLM *when* failure happened — ask *what should have happened instead*. Use the counterfactual as a hindsight-style training signal. More ambitious; design + prototype tonight, not a full implementation.

**Plus literature** — deep dive on Sharony's paper for differentiation, build the bibliography for the paper.

---

## 2. Compute + auth state

| Resource | Status | Where |
|---|---|---|
| Modal CLI | ✅ installed | `~/IsaacLab/.venv311/bin/modal` (also in project venv after step 3 below) |
| Modal workspace | ✅ `agile-quadrupeds` (active) — this is where credits live | `~/.modal.toml` |
| Modal secret `semantic-per-secrets` | ⚠️ **NOT YET CREATED in agile-quadrupeds** — user must create (§3) | — |
| W&B | ✅ auth via `~/.netrc` (no need to `wandb login`) | — |
| W&B project | `RL_project` (same as teammate, use distinct run_name prefixes) | — |
| gh CLI | ✅ logged in as DJRGVC | — |
| Project venv | ✅ at `~/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/.venv` | created by handoff prep |
| GPU | RTX 5070 Ti, 16GB | not load-bearing — Modal does training |

---

## 3. Preflight checks (run before firing agents)

```bash
cd ~/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185
source .venv/bin/activate

# 1. Verify imports
python -c "import torch, gymnasium, gymnasium_robotics, modal, wandb, openai; print('ok')"

# 2. Modal workspace
modal profile current   # must show agile-quadrupeds

# 3. Modal secret — MUST exist before any modal run
modal secret list | grep semantic-per-secrets
```

**If step 3 returns nothing, STOP and ask Daniel to run:**

```bash
modal secret create semantic-per-secrets \
    OPENAI_API_KEY=<his openai key> \
    WANDB_API_KEY=<from ~/.netrc — line under api.wandb.ai> \
    WANDB_ENTITY=djrgvc \
    WANDB_PROJECT=RL_project
```

(Or via Modal dashboard at modal.com/secrets — workspace agile-quadrupeds — name `semantic-per-secrets`.)

Once the secret exists, all 6 agents can fire.

---

## 4. The 6-agent plan

| Agent | Worktree | Modal? | Deliverable |
|---|---|---|---|
| **A1** — HER baselines + ablation launch | yes | yes (launch + detach) | HER/HER+PER/HER+SemanticPER configs implemented + smoke-tested, full sweep launched on Modal, live on W&B |
| **A2** — Oracle v3 + bidirectional priority | yes | yes (short verify) | Contact-aware oracle, BidirectionalSemanticBuffer (success+failure boost), smoke test, design doc |
| **C1** — Counterfactual VLM prompting | yes | no | Working prompts that elicit "what should have happened" from GPT-4o + Claude; eval on 5–10 failed episodes from existing W&B runs |
| **C2** — Counterfactual → SAC mechanism design | yes | no | Design doc + minimal prototype for VLM-counterfactual-as-HER-relabel; not a full impl |
| **L1** — Sharony deep-dive + differentiation map | no | no | Full breakdown of 2602.01915, line-by-line method comparison table, citation-ready related work paragraph, our novelty claims |
| **L2** — Bibliography (credit assignment + HER SOTA + VLM-in-RL) | no | no | Annotated bib of 15–20 papers grouped by theme |

All 6 launch with `model: "opus"` and `run_in_background: true`. Implementation agents (A1, A2, C1, C2) use `isolation: "worktree"`.

Hard deadline: **20:50 PDT** for all reports (last 10 minutes for you to synthesize).

---

## 5. Pre-baked agent prompts — paste these into `Agent` calls

When you're ready, fire all 6 in a single message with 6 parallel `Agent` tool calls. Each prompt is self-contained — agents do not see this handoff.

### Agent A1 — HER baselines + ablation launch

```
You are agent A1 working on an RL research project at /home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185 (RL_project_185, branch main, owned by user DJRGVC). Goal: aim for NeurIPS-quality work by end of week. You are on Daniel's PC (Ubuntu, Modal workspace agile-quadrupeds, W&B already authed via ~/.netrc).

CONTEXT
The project tests Semantic PER (VLM-guided failure-window replay boosting) on Gymnasium-Robotics Fetch tasks with SAC. The existing ablation compares Uniform / PER / Semantic PER (GPT-4o) / Semantic PER (Oracle heuristic). HER is THE standard baseline for Fetch envs and is currently missing. her_buffer.py exists but is untested and not in modal_app.py's METHODS list. Without HER baselines our paper is outside the published comparison space.

DELIVERABLE BY 20:50 PDT
1. Verify her_buffer.py works (push/sample/finish_episode), fix bugs if any.
2. Smoke-test (10k steps locally with reduced eval) these configs:
   - configs/her.yaml
   - configs/her_per.yaml
   - configs/her_semantic_per.yaml (with vlm_provider=heuristic to avoid API cost)
3. Edit modal_app.py's METHODS list in run_ablation() to add HER variants. Use heuristic localizer (no OpenAI calls) for cost. Keep ENVS=[FetchPickAndPlace-v4, FetchPush-v4, FetchSlide-v4] and SEEDS=[42, 123, 999].
4. Add WANDB_PROJECT=RL_project tagging so runs are findable in user's W&B. Add a wandb run_name prefix like "her_baselines_<method>_<env>_seed<N>" so we can filter.
5. Launch the full sweep on Modal with --detach. Capture the modal app ID + a representative W&B URL.
6. Write report at agent_reports/A1_her_baselines.md with: Changes Made / Files Modified / Smoke Test Results / Modal App ID / W&B Filter URL / Known Issues / Next Steps.

CONSTRAINTS
- Use the project venv: source .venv/bin/activate
- DON'T break existing configs.
- DON'T launch the GPT-4o VLM variant tonight (cost). Use heuristic localizer only.
- If a smoke test fails, debug it — don't launch broken configs to Modal.
- Modal secret semantic-per-secrets must exist in agile-quadrupeds workspace before launching. If it doesn't, abort the Modal launch step and document the issue in your report (everything else still ships).
- Work in a git worktree on branch agent/a1-her-baselines (you should have been started with worktree isolation — confirm with `git status` and `git branch --show-current`).

REPORT FORMAT
The report is what Daniel will read at 21:00 to present to teammates. Be CONCRETE: file paths, line numbers, exact run names, Modal app IDs, W&B URLs. No fluff.
```

### Agent A2 — Oracle v3 + bidirectional priority

```
You are agent A2 working on RL_project_185 (Semantic PER project) at /home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185. Goal: NeurIPS-quality work by end of week.

CONTEXT
The current GoalDistanceLocalizer (src/vlm/localizer.py) is two-phase: ballistic detection (for FetchSlide throws) + argmin closest-approach (for contact tasks). It improved over v1 but still doesn't reason about CONTACT events. Meanwhile, a Feb 2026 paper (arXiv 2602.01915, Sharony et al., "VLM-Guided Experience Replay") boosts SUCCESS-like transitions. Our pitch differentiates by boosting FAILURE-causing transitions. The natural test of this pitch is a BIDIRECTIONAL variant that does BOTH and is compared against each direction alone.

DELIVERABLE BY 20:50 PDT
1. Extend GoalDistanceLocalizer in src/vlm/localizer.py with a CONTACT-AWARE phase:
   - Use ee_pos vs object_pos proximity from the observation vector (the Fetch obs structure has ee_pos at known indices — check src/envs/wrappers.py FlattenGoalObs)
   - Detect "contact loss" timesteps (ee was near object then moved away)
   - For contact-loss tasks (Push, PickPlace), prefer contact-loss timestep when one is detected; fall back to ballistic / argmin
   - Call this version Oracle v3
   
2. Implement BidirectionalSemanticBuffer in src/buffers/bidirectional_buffer.py:
   - Two per-slot weight arrays: success_weight and failure_weight (both default 1.0)
   - failure_window applies failure_boost (e.g., 10.0) like existing semantic_per
   - success_window applies success_boost (e.g., 10.0) around an oracle-identified "best progress" timestep (argmax distance reduction over a window) — this is our proxy for what Sharony's VLM would identify
   - Final priority: TD_priority × failure_weight × success_weight
   - On a fully-successful episode, only success_weight is boosted (failure_window doesn't apply)
   - On a failed episode, both can apply: success_weight on the best-progress timestep, failure_weight on the failure timestep
   
3. Add configs/bidir.yaml (inherit from base, type=bidir, both boosts)
4. Wire it into src/buffers/__init__.py make_buffer factory and train.py
5. Smoke test (10k steps) on FetchPush-v4 + FetchSlide-v4 (the two envs where directions might differ most)
6. Launch one Modal verification run per env (50k steps with --detach) to confirm it doesn't crash
7. Write report at agent_reports/A2_oracle_v3_bidirectional.md with: Design Rationale / Implementation Details / Smoke Test Output / Modal Run IDs / Open Questions

CONSTRAINTS
- Project venv: source .venv/bin/activate
- Worktree: branch agent/a2-oracle-bidir
- DON'T modify SemanticPERBuffer in place — create new BidirectionalSemanticBuffer as a sibling.
- Modal secret semantic-per-secrets must exist in agile-quadrupeds workspace before launching. If not, document and skip Modal step.
- Reasoning over implementation: explain WHY contact-aware is better than ballistic+argmin for Push/Pick before coding.

REPORT FORMAT
Be concrete: code locations, exact priority computation, sample output from smoke test, Modal IDs, what you'd test next.
```

### Agent C1 — Counterfactual VLM prompting

```
You are agent C1 working on RL_project_185 at /home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185. Path C of our NeurIPS-track research: VLM Counterfactual Reasoning for Credit Assignment.

CONTEXT
Current VLM (src/vlm/localizer.py) asks GPT-4o "which frame shows the failure?" Output is a single timestep, used to boost replay priority. Path C asks a DIFFERENT question: "given this failed trajectory, what action at frame K WOULD HAVE LED TO SUCCESS?" The output is a counterfactual — a desired action / desired goal / desired state — that we can use as a hindsight relabeling target. This is genuinely novel (no published work does VLM-counterfactual-for-RL as far as our lit scan found).

Tonight is PROTOTYPING. Don't try to integrate with SAC — agent C2 is designing that mechanism. You produce the VLM-side: working prompts + a testable CLI.

DELIVERABLE BY 20:50 PDT
1. Design 2-3 prompt variants that elicit counterfactual reasoning from GPT-4o (and try Claude Opus 4.7 as a backup):
   - Variant A: "Describe in 1 sentence what the robot should have done differently"
   - Variant B: "Specify a corrective action vector (Δx, Δy, Δz, gripper) at the critical frame"
   - Variant C: "What 3D position (achieved_goal) should the object have reached at the critical frame for the episode to succeed?"
2. Build src/vlm/counterfactual.py with a CounterfactualLocalizer class that:
   - Takes keyframes + task_description + (optionally) the failure_timestep already identified
   - Queries the VLM with one or all prompt variants
   - Parses structured JSON output: {"corrective_position": [x,y,z], "corrective_action": [dx,dy,dz,grip], "explanation": "..."}
   - Returns the counterfactual + confidence
3. Build scripts/test_counterfactual.py that:
   - Loads ~5–10 failed episodes from existing W&B runs (use wandb api — entity djrgvc, project RL_project, find runs with method=semantic_per_heuristic_v2)
   - Reconstructs keyframes either from W&B logged images or by re-rolling out the policy (the W&B logger logs vlm/failure_keyframe images — use those)
   - Runs each counterfactual prompt variant against each episode
   - Saves outputs to agent_reports/C1_counterfactual_outputs.json
4. Eval whether the VLM's counterfactual is plausible (you can use Claude Opus 4.7 as a judge — does the counterfactual physically make sense?).
5. Write report at agent_reports/C1_counterfactual_prompts.md with: Prompt Designs / Example Outputs / Plausibility Analysis / Failure Modes / Recommended Prompt Variant for Path C

CONSTRAINTS
- Project venv: source .venv/bin/activate
- Worktree: branch agent/c1-counterfactual-prompts
- OpenAI key must be in env (export OPENAI_API_KEY=...). If not set, fall back to Claude only via anthropic SDK (ANTHROPIC_API_KEY).
- Budget cap: don't make more than ~30 VLM calls total tonight. Each call is ~$0.05 → cap at $1.50.
- DON'T touch the existing localizer.py — add counterfactual.py as a new file.

REPORT FORMAT
Show actual prompt+output pairs. Be honest about which prompt variant produces plausible outputs and which produce hallucinations.
```

### Agent C2 — Counterfactual → SAC mechanism design

```
You are agent C2 working on RL_project_185 at /home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185. Path C theoretical piece: how does a VLM counterfactual feed into the SAC training loop?

CONTEXT
Agent C1 is producing VLM-generated counterfactuals: "at frame K the robot should have reached position (x*, y*, z*)." Your job is to DESIGN how this signal trains the policy — and produce a minimal prototype, not a full implementation.

The natural candidates:
(i) Counterfactual HER-style relabeling: treat (x*, y*, z*) as a hindsight desired_goal, recompute reward against it, push synthetic transitions into the buffer. This is HER but with VLM-imagined goals instead of achieved goals.
(ii) Counterfactual reward shaping: add a dense bonus `r += -||achieved_goal - counterfactual||` for transitions near frame K.
(iii) Counterfactual-guided exploration: bias the policy toward the counterfactual direction at the critical frame using a learned auxiliary head.

DELIVERABLE BY 20:50 PDT
1. Survey-style mini-analysis (~3-5 paragraphs): how does prior work integrate language/visual feedback into RL updates? Use the alphaxiv MCP to find 3-5 relevant recent papers. Key keywords: "VLM-as-critic", "language conditioned RL", "HER relabeling variants", "VLM hindsight", "synthetic experience replay".
2. Compare the three candidates above on: theoretical grounding, implementation cost, expected effect, novelty vs Sharony 2602.01915.
3. Pick the most promising for our 6-day timeline. Justify.
4. Write a minimal prototype: a stub class in src/buffers/counterfactual_buffer.py that extends HERBuffer and overrides finish_episode to use VLM-counterfactual goals instead of (or in addition to) achieved-future goals. Just the skeleton + docstrings + key method signatures. No training run needed.
5. Identify 2-3 critical experiments that would validate the picked approach.
6. Write report at agent_reports/C2_counterfactual_mechanism.md with: Lit Survey / Three Candidates / Recommendation + Justification / Prototype Code / Validation Plan / Risks

CONSTRAINTS
- Project venv: source .venv/bin/activate
- Worktree: branch agent/c2-counterfactual-mechanism
- DON'T over-engineer. Skeleton + design doc, not full implementation. Agent C1 owns the VLM side.
- DON'T write training code that runs — just stub it.

REPORT FORMAT
Heavy on rationale, light on code. The audience (Daniel) needs to decide tomorrow if Path C is worth pursuing in the remaining 5 days. Your report is the decision input.
```

### Agent L1 — Sharony deep-dive + differentiation map

```
You are agent L1, a research literature analyst for RL_project_185. CRITICAL TASK: deep-dive on the paper that potentially scooped our work.

CONTEXT
The user (Daniel) is targeting NeurIPS-quality work by end of week on "VLM-guided failure localization for prioritized experience replay." A paper published Feb 2, 2026 — arXiv 2602.01915, Sharony, Jurgenson, Krupnik, Di Castro, Mannor — does much of the high-level pitch. We need to know EXACTLY what they did, where they overlap with us, and where we can claim novelty.

DELIVERABLE BY 20:50 PDT
1. Use the alphaxiv MCP (mcp__alphaxiv__get_paper_content with url=https://arxiv.org/abs/2602.01915) and arxiv-latex MCP if needed to extract: methodology, experimental setup, baselines, ablations, claimed contributions, code release status.
2. Find their GitHub if released (search arxiv abstract + the alphaxiv content).
3. Build a method-comparison table with these rows (ours vs theirs):
   - Signal direction (failure vs success)
   - Granularity (per-clip vs per-timestep)
   - Blending (multiplicative TD-weight vs mixture-with-uniform)
   - VLM model (GPT-4o vs Perception-LM 1B)
   - VLM cost model (API per-call vs frozen async worker)
   - Benchmark (Fetch vs OGBench+MiniGrid)
   - Headroom analysis (oracle baseline vs no oracle)
4. Identify their concurrent/prior work citations for "VLM-in-replay" — anyone else doing this?
5. Write 3-4 differentiation claims our paper can credibly make. Each claim with the evidence we'd need.
6. Write a citation-ready related-work paragraph (~150 words) framing our work against theirs.
7. Report at agent_reports/L1_sharony_differentiation.md with sections: Paper Summary / Method Comparison Table / Concurrent Work Citations / Our Differentiation Claims / Related Work Paragraph / Remaining Questions.

CONSTRAINTS
- DON'T write code. Read-only analysis task.
- DON'T spawn sub-agents. You are an analyst, not a coordinator.
- If alphaxiv tools return cached/old data, also try fetching from arxiv.org directly via WebFetch.

REPORT FORMAT
Tight, structured, citation-ready. Daniel will use this verbatim in the related work section tomorrow.
```

### Agent L2 — Bibliography (credit assignment + HER SOTA + VLM-in-RL)

```
You are agent L2, a research bibliography builder for RL_project_185.

CONTEXT
We need a citation-ready annotated bibliography for our paper. Three threads matter most:
1. Credit assignment in deep RL (counterfactual reasoning, return decomposition, causal influence) — supports Path C's framing
2. HER variants + recent goal-conditioned RL SOTA on sparse-reward manipulation — supports our baseline competitiveness (we MUST cite Next-Future arXiv 2504.11247 and Contact Energy Hindsight 2312.02677)
3. VLM/LLM/foundation-model integration with RL (reward, critic, planner, replay) — supports our Related Work framing

DELIVERABLE BY 20:50 PDT
1. Use the alphaxiv MCP (mcp__alphaxiv__discover_papers) and arxiv-latex MCP to find 15-20 papers across the three threads. Focus on 2024-2026 publications.
2. For each paper, produce:
   - Citation (BibTeX style)
   - 2-3 sentence summary
   - One sentence on relevance to our work
   - Thread tag (credit-assignment / her-sota / vlm-in-rl)
3. Specifically include and characterize these papers (MUST CITE):
   - arXiv 2504.11247 (Next-Future)
   - arXiv 2312.02677 (Contact Energy Hindsight)
   - arXiv 2312.01072 (Credit Assignment Survey - DeepMind)
   - arXiv 2602.01915 (Sharony VLM-RB — handled by L1 too, briefly include here)
   - arXiv 2603.16065 (Large Reward Models)
   - arXiv 2407.10341 (KAGI — Chelsea Finn affordance-guided)
4. Identify any paper that has done VLM-counterfactual-for-RL specifically (this would be a Path C scoop — surface it loudly if found).
5. Report at agent_reports/L2_bibliography.md with the annotated bib grouped by thread + a 1-paragraph synthesis of where the field is and where our work fits.

CONSTRAINTS
- DON'T write code.
- DON'T duplicate L1's deep dive on Sharony — briefly cite, point at L1's report.
- If you find a Path C scoop, flag it at the TOP of your report.

REPORT FORMAT
BibTeX entries + annotations. Daniel will paste these into Zotero / Overleaf tomorrow.
```

---

## 6. After firing: monitor and synthesize

While agents run (background, you'll get notifications as each completes), you can:
- Run `git worktree list` to see active worktrees
- Check `agent_reports/` for incremental writes
- Use `modal app list` to verify Modal jobs spawned by A1/A2 are running
- Use `wandb` API to verify W&B runs are streaming

**At 20:50 PDT** (or as soon as all 6 reports exist):

Read all 6 reports. Write `agent_reports/9pm_presentation.md` as a tight summary Daniel will share with Parshawn and Matei:

1. **Path A status** — what HER baselines were launched (A1), bidirectional design (A2), expected results
2. **Path C status** — counterfactual prompts working? (C1), design recommendation (C2)
3. **Differentiation from Sharony** — pulled from L1
4. **Recommended thesis framing for the paper** — synthesizing A + C with the L1/L2 lit
5. **Open decisions for the team** — what needs Daniel/Parshawn/Matei agreement tomorrow
6. **Tomorrow's plan** — concrete next steps

Keep it under 1 page. Daniel is presenting at 21:00; this is his prep.

---

## 7. Things NOT to do

- Don't re-spawn agents that are still running.
- Don't merge worktree branches tonight — Daniel will review tomorrow.
- Don't push commits to origin/main — agents commit on their own branches; user merges later.
- Don't launch the GPT-4o VLM variant on Modal tonight (API cost). Use heuristic localizer.
- Don't burn tokens re-summarizing the audit / Sharony scoop / paths — they're in §1.
- Don't ask Daniel for clarifying questions he already answered. He confirmed: Path A + Path C in parallel, 2 agents each, plus 2 lit-review agents. ~9pm PDT deadline. Modal in agile-quadrupeds workspace. W&B project RL_project.

---

**Good luck. Fire the agents.**
