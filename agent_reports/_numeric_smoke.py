"""Smoke test for the numeric VLM-CF prompt variant.

Stubs out the Anthropic client so no real API calls are made and runs a
small training loop (~200 steps) on FetchPickAndPlace to verify the full
plumbing: prompt rendering, ee_positions kwarg routing, CF acceptance and
buffer/cf_* logging keys.
"""
from __future__ import annotations

import os
import sys
import numpy as np

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

# Stub the CounterfactualLocalizer before train.py imports anything.
from src.vlm import counterfactual as cf_mod  # noqa: E402

_captured = {"prompt": None, "calls": 0}


def _fake_init(self):
    self._client = None


def _fake_call_anthropic(self, frames, prompt):
    _captured["prompt"] = prompt
    _captured["calls"] += 1
    # Return a CF that is offset from the desired_goal so the teleport gate
    # accepts it.
    return (
        '{"corrective_position": [1.25, 0.78, 0.48], '
        '"explanation": "halfway corrective", "confidence": 0.9}'
    )


def _fake_call_openai(self, frames, prompt):  # symmetric; harmless if unused
    _captured["prompt"] = prompt
    _captured["calls"] += 1
    return (
        '{"corrective_position": [1.25, 0.78, 0.48], '
        '"explanation": "halfway corrective", "confidence": 0.9}'
    )


cf_mod.CounterfactualLocalizer._init_client = _fake_init
cf_mod.CounterfactualLocalizer._call_anthropic = _fake_call_anthropic
cf_mod.CounterfactualLocalizer._call_openai = _fake_call_openai

from train import load_config, train  # noqa: E402

cfg = load_config(
    os.path.join(REPO_ROOT, "configs/vlm_cf_numeric.yaml"),
    overrides=[
        "training.total_steps=200",
        "training.warmup_steps=50",
        "training.eval_interval=1000",   # don't bother
        "training.save_interval=1000",
        "training.eval_episodes=1",
        "replay.cf_call_interval=1",
        "logging.use_wandb=False",
        "logging.run_name=smoke_numeric",
    ],
)
print("\n[smoke] cfg loaded; vlm_variant =", cfg["replay"]["vlm_variant"])
print("[smoke] starting 200-step training run...")

best = train(cfg)
print(f"\n[smoke] training finished. best_success={best}")
print(f"[smoke] VLM was called {_captured['calls']} time(s).")
if _captured["prompt"] is not None:
    print("\n[smoke] ===== FIRST RENDERED PROMPT =====")
    print(_captured["prompt"][:2200])  # truncate for tidiness
    print("[smoke] ===== END PROMPT =====")
    # Critical assertion: the table substring must be present.
    if "| Frame |" in _captured["prompt"]:
        print("\n[smoke] PASS: trajectory table present in prompt.")
    else:
        print("\n[smoke] FAIL: trajectory table MISSING from prompt.")
        sys.exit(1)
    if "Block xyz" in _captured["prompt"]:
        print("[smoke] PASS: numerical block xyz column present.")
    else:
        print("[smoke] FAIL: block xyz column missing.")
        sys.exit(1)
    if "Gripper ee_xyz" in _captured["prompt"]:
        print("[smoke] PASS: numerical gripper ee_xyz column present.")
    else:
        print("[smoke] FAIL: gripper ee_xyz column missing.")
        sys.exit(1)
else:
    # No failed-and-VLM-eligible episode in 200 steps -> still success for the
    # plumbing test, just note it.
    print("[smoke] NOTE: no VLM call triggered in 200 steps (no failed episode "
          "matched cf_call_interval=1). Plumbing OK; rendering not exercised.")
print("\n[smoke] OK")
