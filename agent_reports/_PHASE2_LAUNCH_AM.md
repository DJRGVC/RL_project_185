# Phase 2 (Verified-CF) Modal launch — AM handoff

**Agent:** Opus 4.7, branch `agent/pathc-lead`
**Timestamp:** 2026-05-12 10:28 PDT
**Budget:** 45 min (used ~30 min on three relaunches due to env-var conflicts)

---

## Step 1 — Modal app cleanup (DONE)

### Stopped apps

| App ID | Description | Reason for stop | Tasks killed |
|---|---|---|---|
| `ap-PWMTBsinFWdaAK048ySfBV` | semantic-per, ephemeral-detached, created 2026-05-11 22:20 PDT (~13h old) | Daniel flagged as "definitely won't be helpful"; well past 6h staleness threshold. | 9 |
| `ap-OCyr832mvzGOvjyePo9qjP` | semantic-per Phase 2 launch attempt #1 (10:25 PDT) | All 18 tasks crashing on `ANTHROPIC_API_KEY not set` — Modal secret was missing the Anthropic key. | 18 (all crashed on init) |
| `ap-dzTbfB1VPzyhx73lN1Jles` | semantic-per Phase 2 launch attempt #2 (10:26 PDT) | All 18 tasks crashing on `ImportError: Cannot use EGL rendering platform` — Modal secret rebuild from local `.env` injected `MUJOCO_GL=egl` (correct for the local 5070 Ti, wrong for Modal). Self-terminated when retries exhausted. | 18 (all crashed on env init) |

Verified all three are `stopped` via `modal app list`.

---

## Step 2 — B2 patch verification (NO NEW PATCH REQUIRED)

`modal_app.py` already had the B2 W&B-entity override at lines 92-93:

```python
os.environ["WANDB_PROJECT"] = "RL_project"
os.environ["WANDB_ENTITY"] = "d-grant-uc-berkeley"
```

…placed at line 92-93 **before** `from train import load_config, train` at line 103. Verified via `inspect.getsource(modal_app.train_remote.get_raw_f())` and confirmed visually in runtime logs:

```
wandb: Currently logged in as: d-grant (d-grant-uc-berkeley) to https://api.wandb.ai.
wandb: Syncing run path_c_vlm_cf_pp_s42_seed42
```

The morning-consolidation agent's claim "B2 still not patched" was incorrect — the 01:45 attempt **did** land. No additional commit needed for B2.

### NEW PATCH: MuJoCo env override (commit `871a5c3`)

The relaunches uncovered a separate regression: when I recreated `semantic-per-secrets` via `modal secret create --from-dotenv .env --force` to add `ANTHROPIC_API_KEY`, the upload also injected `MUJOCO_GL=egl` from the local `.env`. The Modal image bakes in `MUJOCO_GL=osmesa` + `PYOPENGL_PLATFORM=osmesa`, but secret env-vars take precedence at container start, so MuJoCo tried to load EGL (no display, no EGL libs in image) → `ImportError`.

Fix in `modal_app.py` `train_remote` (lines 96-102, before `from train` import):

```python
os.environ["MUJOCO_GL"] = "osmesa"
os.environ["PYOPENGL_PLATFORM"] = "osmesa"
```

Commit: `871a5c3 Modal: force MUJOCO_GL=osmesa override in train_remote` on `agent/pathc-lead`.

---

## Step 3 — Phase 2 launch (LIVE)

**App ID:** `ap-bLMnC0sqx6kVCe7oAERWUQ`
**Modal dashboard:** https://modal.com/apps/agile-quadrupeds/main/ap-bLMnC0sqx6kVCe7oAERWUQ
**Launched:** 2026-05-12 10:27 PDT
**Runs spawned:** 18 (9 vlm_cf + 9 verified_cf across 3 envs × 3 seeds)
**Tasks running:** 10/18 concurrent (Modal account A10G concurrency cap); 8 queued.

### W&B URL

Per the actual code path (`run_path_c_phase2` does NOT inject per-run tags; tags come from configs):
- **As printed by code:** https://wandb.ai/d-grant-uc-berkeley/RL_project?tags=path_c_overnight_2026-05-11
- **As Daniel mentioned in handoff (`path_c_vlm_2026-05-12`):** would not match — that tag is not anywhere in the plan or configs.
- **Most reliable filter:** filter by run-name prefix `path_c_vlm_cf_` and `path_c_vlm_vcf_` (e.g., `path_c_vlm_cf_pp_s42_seed42` already heart-beating per logs).

### Heartbeat confirmed

Sample log evidence (10:27 PDT):
- `wandb: Syncing run path_c_vlm_cf_pp_s42_seed42` → Anthropic-using run, sonnet-4-5 detected.
- `wandb: Syncing run path_c_vlm_cf_push_s42_seed42` → OpenAI-using run, gpt-4o-mini detected.
- `2026-05-12 17:27:48 | INFO | Starting training: 500,000 steps`
- W&B login resolved to `d-grant (d-grant-uc-berkeley)` (B2 patch confirmed working).

### Expected completion

- 500k steps × ~10 parallel A10G = roughly 90 min wall-clock for first wave of 10; remaining 8 start as slots free.
- **ETA all 18 runs done:** 10:27 + ~120 min = **~12:30 PDT** (conservative; could be 12:00 if compute is unloaded).

---

## Errors encountered (resolved)

1. **`ANTHROPIC_API_KEY not set`** — Modal secret didn't include the Anthropic key (modal_app.py docstring only listed OPENAI/WANDB). Resolved via `modal secret create semantic-per-secrets --from-dotenv .env --force`.
2. **`Cannot use EGL rendering platform`** — Side-effect of (1): the `.env`-based secret upload injected `MUJOCO_GL=egl`. Resolved with runtime override in `train_remote` (commit `871a5c3`).

---

## What to check next (operator)

1. ~11:00 PDT: spot-check that W&B has heartbeats from at least the 10 first-wave runs at step >5k.
2. ~12:00 PDT: confirm queued 8 runs have started (Modal app should still be `running` with tasks rotating).
3. ~12:30 PDT: pull eval-success curves and assemble Phase 2 results table.

## Constraints honored

- Did NOT touch any local Path A or Oracle-CF processes.
- All Modal stops logged with reasons before execution.
- Used venv (`source .venv/bin/activate`) for every modal CLI call.
- Patch committed to `agent/pathc-lead` (not main).
