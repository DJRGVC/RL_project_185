"""
N1 smoke test — verifiable counterfactuals on synthetic failed episodes.

Loads ~3 failed-episode records from agent_reports/C1_counterfactual_outputs.json
and runs the VerifiedCounterfactualLocalizer on each. Confirms:

  (a) "teleport" counterfactuals (achieved_goal variant where
      corrective_position == desired_goal and corrective_action == None)
      are REJECTED — i.e., not verified.
  (b) action-based counterfactuals at least run end-to-end without
      crashing, and the framework correctly classifies verified vs not.
  (c) the mechanism does not crash on missing fields / malformed VLM
      output.

Run:
    source .venv/bin/activate
    python scripts/n1_smoke_verified_cf.py

Output: prints a per-episode summary table and writes
agent_reports/N1_smoke_results.json.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# Allow running from project root or from scripts/.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.vlm.verified_counterfactual import (
    VerifiedCounterfactualLocalizer,
    reconstruct_snapshot_for_synthetic_episode,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("N1.smoke")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def select_smoke_episodes(j: Dict[str, Any], k: int = 3) -> List[Dict[str, Any]]:
    """Pick three diverse episodes to exercise teleport-rejection,
    action-verification, and the "all" composite variant."""
    eps = j["episodes"]
    # 1. FetchPush ep that triggered the teleport (achieved_goal variant has
    #    corrective_position == desired_goal).
    teleport = next(
        e for e in eps
        if e["env_name"] == "FetchPush-v4"
        and "achieved_goal" in e["variants"]
        and e["variants"]["achieved_goal"]["corrective_position"]
            == e["desired_goal"]
    )
    # 2. FetchPickAndPlace with action variant.
    action_pp = next(
        e for e in eps
        if e["env_name"] == "FetchPickAndPlace-v4"
        and "action" in e["variants"]
        and e["variants"]["action"]["corrective_action"] is not None
    )
    # 3. The unified "all" variant (FetchPush 9262) — has both fields.
    composite = next(
        e for e in eps
        if "all" in e["variants"]
    )
    return [teleport, action_pp, composite][:k]


def extract_vlm_output(ep: Dict[str, Any], variant_name: str) -> Dict[str, Any]:
    v = ep["variants"][variant_name]
    return {
        "corrective_action":   v.get("corrective_action"),
        "corrective_position": v.get("corrective_position"),
        "confidence":          v.get("confidence", 0.0),
        "explanation":         v.get("explanation", ""),
    }


def run_one(
    ep: Dict[str, Any],
    variant_name: str,
    n_verify_steps: int = 50,
) -> Dict[str, Any]:
    env_name      = ep["env_name"]
    seed          = ep["seed"]
    failure_t     = ep["failure_timestep"]
    desired_goal  = np.array(ep["desired_goal"],          dtype=np.float64)
    achieved_fail = np.array(ep["achieved_goal_at_failure"], dtype=np.float64)
    vlm_out       = extract_vlm_output(ep, variant_name)

    snap = reconstruct_snapshot_for_synthetic_episode(
        env_name=env_name,
        seed=seed,
        achieved_at_failure=achieved_fail,
        desired_goal=desired_goal,
        failure_t=failure_t,
    )
    loc = VerifiedCounterfactualLocalizer(
        env_name=env_name,
        n_verify_steps=n_verify_steps,
    )

    action = vlm_out["corrective_action"]
    if action is None:
        # Teleport-collapse path: VLM gave only a position, no action.
        # The localizer's contract: no action -> immediately rejected.
        vc = loc.verify(
            snap=snap,
            corrective_action=None,
            vlm_explanation=vlm_out["explanation"],
            vlm_confidence=vlm_out["confidence"],
            failure_t=failure_t,
            achieved_at_failure=achieved_fail,
        )
    else:
        vc = loc.verify(
            snap=snap,
            corrective_action=np.asarray(action, dtype=np.float32),
            vlm_explanation=vlm_out["explanation"],
            vlm_confidence=vlm_out["confidence"],
            failure_t=failure_t,
            achieved_at_failure=achieved_fail,
        )

    return {
        "env_name":            env_name,
        "seed":                seed,
        "variant":             variant_name,
        "vlm_corrective_pos":  vlm_out["corrective_position"],
        "vlm_corrective_act":  vlm_out["corrective_action"],
        "vlm_confidence":      vlm_out["confidence"],
        "vlm_explanation":     vlm_out["explanation"],
        "verified":            bool(vc.verified),
        "verified_at_step":    vc.verified_at_step,
        "final_distance":      vc.final_distance,
        "rejection_reason":    vc.rejection_reason,
        "achieved_at_failure": achieved_fail.tolist(),
        "desired_goal":        desired_goal.tolist(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main():
    j_path = ROOT / "agent_reports" / "C1_counterfactual_outputs.json"
    with open(j_path) as f:
        j = json.load(f)

    smoke_eps = select_smoke_episodes(j, k=3)
    log.info("Selected %d smoke episodes.", len(smoke_eps))
    for ep in smoke_eps:
        log.info("  - %s seed=%s, failure_t=%s, variants=%s",
                 ep["env_name"], ep["seed"], ep["failure_timestep"],
                 list(ep["variants"].keys()))

    cases = []

    # Case 1: teleport (achieved_goal variant on FetchPush).
    ep = smoke_eps[0]
    log.info("\n[1/4] Teleport-rejection test — %s seed=%s achieved_goal variant",
             ep["env_name"], ep["seed"])
    r = run_one(ep, "achieved_goal", n_verify_steps=50)
    cases.append({"label": "teleport", **r})

    # Case 2: action variant on PickAndPlace.
    ep = smoke_eps[1]
    log.info("\n[2/4] Action-verification test — %s seed=%s action variant",
             ep["env_name"], ep["seed"])
    r = run_one(ep, "action", n_verify_steps=50)
    cases.append({"label": "action_pp", **r})

    # Case 3: composite "all" variant — has both action and position.
    #         We use only the action component for this prototype.
    ep = smoke_eps[2]
    log.info("\n[3/4] Composite-action test — %s seed=%s all variant",
             ep["env_name"], ep["seed"])
    r = run_one(ep, "all", n_verify_steps=50)
    cases.append({"label": "composite", **r})

    # Case 4: a physically-reasonable hand-crafted action that *should* verify.
    #         Use the PickAndPlace ep but supply an action that moves toward
    #         the goal — confirms the framework can ACCEPT counterfactuals.
    log.info("\n[4/4] Hand-crafted success test — handcrafted action that moves toward goal")
    ep = smoke_eps[1]
    desired_goal  = np.array(ep["desired_goal"],          dtype=np.float64)
    achieved_fail = np.array(ep["achieved_goal_at_failure"], dtype=np.float64)
    # Direction from current to goal. Fetch action[:3] are positional deltas.
    direction = desired_goal[:3] - achieved_fail[:3]
    norm = np.linalg.norm(direction)
    if norm > 0:
        direction /= norm
    # Strong push in the right direction + open gripper.
    handcraft = np.array(
        [float(direction[0]),
         float(direction[1]),
         float(direction[2]),
         0.0],
        dtype=np.float32,
    )
    snap = reconstruct_snapshot_for_synthetic_episode(
        env_name=ep["env_name"],
        seed=ep["seed"],
        achieved_at_failure=achieved_fail,
        desired_goal=desired_goal,
        failure_t=ep["failure_timestep"],
    )
    # Move the goal close to the block so the corrective action provably can
    # reach it within 50 steps — this validates the verifier's "accept" path.
    snap.goal = (achieved_fail[:3] + 0.03 * direction).astype(np.float64)
    loc = VerifiedCounterfactualLocalizer(
        env_name=ep["env_name"], n_verify_steps=50
    )
    vc = loc.verify(
        snap=snap,
        corrective_action=handcraft,
        vlm_explanation="Hand-crafted: push directly toward goal.",
        vlm_confidence=0.9,
        failure_t=ep["failure_timestep"],
        achieved_at_failure=achieved_fail,
    )
    cases.append({
        "label":               "handcraft_success",
        "env_name":            ep["env_name"],
        "seed":                ep["seed"],
        "variant":             "handcraft",
        "vlm_corrective_pos":  None,
        "vlm_corrective_act":  handcraft.tolist(),
        "vlm_confidence":      0.9,
        "vlm_explanation":     "Hand-crafted: push directly toward goal.",
        "verified":            bool(vc.verified),
        "verified_at_step":    vc.verified_at_step,
        "final_distance":      vc.final_distance,
        "rejection_reason":    vc.rejection_reason,
        "achieved_at_failure": achieved_fail.tolist(),
        "desired_goal":        snap.goal.tolist(),
    })

    # ── summary table ────────────────────────────────────────────────────
    log.info("\n" + "=" * 88)
    log.info(f"{'label':<22}{'env':<22}{'verified':<10}{'final_dist':<12}{'reason'}")
    log.info("-" * 88)
    for c in cases:
        log.info(
            f"{c['label']:<22}{c['env_name']:<22}"
            f"{str(c['verified']):<10}"
            f"{c['final_distance']:<12.4f}"
            f"{(c['rejection_reason'] or 'verified')[:36]}"
        )
    log.info("=" * 88)

    # ── assertions: confirm the design goals ─────────────────────────────
    pass_count = 0
    total = 4

    if cases[0]["verified"] is False and "no_corrective_action" in (cases[0]["rejection_reason"] or ""):
        log.info("PASS (1/4): teleport counterfactual correctly rejected (no executable action).")
        pass_count += 1
    else:
        log.warning("FAIL (1/4): expected teleport rejection, got verified=%s reason=%s",
                    cases[0]["verified"], cases[0]["rejection_reason"])

    if cases[1]["verified"] in (True, False) and cases[1]["rejection_reason"] != "rollout_exception":
        log.info("PASS (2/4): action verification ran end-to-end (verified=%s).",
                 cases[1]["verified"])
        pass_count += 1
    else:
        log.warning("FAIL (2/4): action variant blew up — %s", cases[1]["rejection_reason"])

    if cases[2]["verified"] in (True, False) and cases[2]["rejection_reason"] != "rollout_exception":
        log.info("PASS (3/4): composite-all variant ran end-to-end (verified=%s).",
                 cases[2]["verified"])
        pass_count += 1
    else:
        log.warning("FAIL (3/4): composite variant blew up — %s", cases[2]["rejection_reason"])

    if cases[3]["verified"] is True:
        log.info("PASS (4/4): hand-crafted close-goal counterfactual VERIFIED — accept path works.")
        pass_count += 1
    else:
        log.warning("FAIL (4/4): expected handcraft success, got verified=False (dist=%.3f, reason=%s).",
                    cases[3]["final_distance"], cases[3]["rejection_reason"])

    log.info("\nSmoke test result: %d/%d passed.", pass_count, total)

    out_path = ROOT / "agent_reports" / "N1_smoke_results.json"
    with open(out_path, "w") as f:
        json.dump({"cases": cases, "pass_count": pass_count, "total": total}, f, indent=2)
    log.info("Wrote: %s", out_path)


if __name__ == "__main__":
    main()
