"""
Oracle counterfactual generators — hand-coded "perfect" CF goals per task.

These are the kill-experiment ceiling. They emulate what a perfect VLM would
say, using ground-truth state (ee_pos, object_pos, actions, desired_goal)
that's already available in the buffer dict — no rendering, no API calls.

Interface (matches CounterfactualHERBuffer with `cf_input_kind='state'`):

    cf_fn(trajectory: dict) -> Optional[List[(frame_index, xyz, confidence)]]

The `trajectory` dict carries (see `_build_trajectory_dict`):
    - 'obs':                (T, obs_dim)       raw flattened obs vectors
    - 'actions':            (T, 4)             actions taken
    - 'achieved_goals':     (T, 3)             == object positions for Fetch
    - 'next_achieved_goals':(T, 3)
    - 'ee_pos':             (T, 3)             obs[:,0:3]
    - 'object_pos':         (T, 3)             == achieved_goals
    - 'desired_goal':       (3,)
    - 'T':                  int
    - 'env_name':           Optional[str]

Each oracle returns *one* CF per episode (most informative frame). Confidence
is 1.0 by construction — these are the privileged ceiling.

Design notes
------------
- FetchPush: classic failure is the agent overshooting / approaching the
  block from the wrong side. The most informative CF frame is when ee-block
  distance is maximised (when the agent has lost its grip on the task);
  the corrective xyz is the midpoint between ee and desired_goal — i.e.
  "stand on the goal-side of the block and push toward it from there".
- FetchPickAndPlace: the agent often pushes the block on the table or
  drops it after lifting. The Sonnet-4.5 insight from C1v2-B is that the
  corrective intermediate waypoint is a *mid-air* point above the goal
  (z + 8cm) — once the block is there, the descent to the goal is trivial.
  We pick the frame just after gripper contact (proxy: first frame where
  the block height drops by >1cm post-warmup), then output the mid-air
  waypoint as the CF.
- FetchSlide: contact is fleeting; the corrective is at the release moment.
  We use a 1D ballistic model: solve x(t) = x0 + v*t - 0.5*mu*g*t^2 for the
  desired puck arrival point, then output the *release position* and
  *release velocity* as a 3D point projected forward (no time integration —
  we relabel the goal, not the action).
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Same shape as CounterfactualHERBuffer's `Counterfactual`.
Counterfactual = Tuple[int, np.ndarray, float]


# Workspace sanity bounds (Fetch suite).
_X_LO, _X_HI = 1.05, 1.55
_Y_LO, _Y_HI = 0.30, 1.20
_Z_LO, _Z_HI = 0.42, 0.95


def _clip_to_workspace(p: np.ndarray) -> np.ndarray:
    """Keep CF goals inside Fetch workspace bounds."""
    return np.array([
        np.clip(p[0], _X_LO, _X_HI),
        np.clip(p[1], _Y_LO, _Y_HI),
        np.clip(p[2], _Z_LO, _Z_HI),
    ], dtype=np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# Per-task oracles
# ─────────────────────────────────────────────────────────────────────────────


def oracle_cf_push(trajectory: Dict[str, Any]) -> Optional[List[Counterfactual]]:
    """FetchPush oracle.

    Strategy: at the frame where the ee-block distance is maximised, output
    a CF that places the block on the line between *the block* and
    desired_goal — i.e. the "the block should be partway to the goal" insight.

    Implementation: cf_xyz = midpoint(block_pos[k], desired_goal). Previously
    used midpoint(ee[k], desired_goal), but at max ee-block divergence the
    ee is in an arbitrary location (agent has lost the block), making that
    midpoint a random workspace region. Using block_pos[k] anchors the CF
    to a physically meaningful state — "the block was actually here, treat
    a point partway to the goal as a useful intermediate target."

    This is a CODE-REVIEWER-flagged bugfix: the prior ee-midpoint variant
    underperformed HER by 0.33 on FetchPush in the 2026-05-11 KILL run.
    """
    ee  = trajectory["ee_pos"]
    obj = trajectory["object_pos"]
    g   = trajectory["desired_goal"]
    T   = trajectory["T"]
    if T < 4:
        return None
    dist_ee_block = np.linalg.norm(ee - obj, axis=1)  # (T,)
    k = int(np.argmax(dist_ee_block))
    # Don't pick a frame in the first 10% (cold-start noise) or after T-2.
    k = int(np.clip(k, max(2, T // 10), T - 2))
    # Use block_pos[k] (not ee[k]) — see docstring.
    cf_xyz = 0.5 * (obj[k] + g)
    cf_xyz = _clip_to_workspace(cf_xyz)
    return [(k, cf_xyz, 1.0)]


def oracle_cf_pick_and_place(
    trajectory: Dict[str, Any],
) -> Optional[List[Counterfactual]]:
    """FetchPickAndPlace oracle.

    Strategy: the agent typically loses the block on descent or after lift.
    The C1v2-B real-data finding (Sonnet 4.5 on actual failed PnP episodes)
    is that the right intermediate goal is a *mid-air* point directly above
    desired_goal, at z + 0.08 m. Once the block sits in that pocket, the
    final descent is a few cm and the sparse reward will fire.

    Implementation: pick the frame where the block first drops by > 1 cm
    after warmup (proxy for "gripper just contacted and lifted then
    failed"). If no such frame, default to T // 2 (mid-episode).
    """
    obj = trajectory["object_pos"]
    g   = trajectory["desired_goal"]
    T   = trajectory["T"]
    if T < 4:
        return None
    z_obj = obj[:, 2]
    z_init = float(z_obj[0])
    # Find first frame where block height is BELOW the initial table-rest
    # height by > 0.005 m AFTER a sustained lift. Use the first lift-then-drop
    # event; if absent, mid-episode.
    lifted = np.where(z_obj > z_init + 0.015)[0]
    if len(lifted) > 0:
        first_lift = int(lifted[0])
        # Look for first drop after the lift.
        post = z_obj[first_lift:]
        drop_idx_local = np.where(np.diff(post) < -0.005)[0]
        if len(drop_idx_local) > 0:
            k = first_lift + int(drop_idx_local[0]) + 1
        else:
            k = first_lift + max(1, len(post) // 2)
    else:
        k = T // 2
    k = int(np.clip(k, max(2, T // 8), T - 2))
    cf_xyz = np.array([g[0], g[1], g[2] + 0.08], dtype=np.float32)
    cf_xyz = _clip_to_workspace(cf_xyz)
    return [(k, cf_xyz, 1.0)]


def oracle_cf_slide(trajectory: Dict[str, Any]) -> Optional[List[Counterfactual]]:
    """FetchSlide oracle.

    Strategy: detect the release frame (puck velocity peaks then plateaus
    while ee-puck distance grows). At that frame, the agent has committed
    to a ballistic trajectory. Output the predicted ballistic terminus as
    the CF — this is the position the puck *will* reach under the friction
    model, which is a useful hindsight goal because the policy already
    produced an action that lands the puck there.

    Implementation: simple ballistic model — assume friction-deceleration
    mu*g with mu ≈ 0.1, g = 9.81 m/s^2 ⇒ a = -0.981 m/s^2 in the puck plane.
    Predict terminus as x_release + v_release * t_stop - 0.5 * a * t_stop^2
    where t_stop = ||v_release|| / a, capped at the episode horizon.
    """
    obj = trajectory["object_pos"]
    g   = trajectory["desired_goal"]
    T   = trajectory["T"]
    dt  = 1 / 25.0       # Fetch step is ~40 ms; use 1/25s as the conservative dt.
    if T < 5:
        return None
    # Approximate velocity by finite diff of object_pos (m/step → m/s).
    v = (np.diff(obj, axis=0)) / dt  # (T-1, 3)
    speed = np.linalg.norm(v[:, :2], axis=1)
    peak_t = int(np.argmax(speed))
    if speed[peak_t] < 0.05:
        # Object barely moved; release event indeterminate. Pick frame T//3.
        k = T // 3
        cf_xyz = obj[min(k + 2, T - 1)].astype(np.float32)
        cf_xyz = _clip_to_workspace(cf_xyz)
        return [(k, cf_xyz, 1.0)]
    # Release frame = peak velocity (mild post-peak deceleration is ballistic).
    k = int(np.clip(peak_t, max(2, T // 8), T - 2))
    v_rel = v[k]
    p_rel = obj[k]
    a_decel = 0.981   # m/s^2 — friction
    # Time to stop (using 2D speed magnitude); cap at remaining horizon * dt.
    t_stop = float(np.linalg.norm(v_rel[:2]) / a_decel)
    t_stop = min(t_stop, (T - k) * dt * 4.0)
    direction_xy = v_rel[:2] / (np.linalg.norm(v_rel[:2]) + 1e-8)
    travel = (np.linalg.norm(v_rel[:2]) * t_stop) - 0.5 * a_decel * t_stop ** 2
    terminus_xy = p_rel[:2] + direction_xy * travel
    cf_xyz = np.array([terminus_xy[0], terminus_xy[1], p_rel[2]], dtype=np.float32)
    cf_xyz = _clip_to_workspace(cf_xyz)
    return [(k, cf_xyz, 1.0)]


def oracle_cf_reach(trajectory: Dict[str, Any]) -> Optional[List[Counterfactual]]:
    """FetchReach oracle (trivial — used only for smoke tests).

    For Reach the achieved_goal == ee_pos. CF at frame T//2 = desired_goal
    minus 5cm in the direction the agent should travel.
    """
    g   = trajectory["desired_goal"]
    ee  = trajectory["ee_pos"]
    T   = trajectory["T"]
    if T < 3:
        return None
    k = T // 2
    direction = g - ee[k]
    n = np.linalg.norm(direction) + 1e-8
    cf_xyz = ee[k] + direction * (1.0 - 0.05 / n)
    return [(k, cf_xyz.astype(np.float32), 1.0)]


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────


_ORACLE_REGISTRY: Dict[str, Callable[[Dict[str, Any]], Optional[List[Counterfactual]]]] = {
    "FetchPush-v4":           oracle_cf_push,
    "FetchPickAndPlace-v4":   oracle_cf_pick_and_place,
    "FetchSlide-v4":          oracle_cf_slide,
    "FetchReach-v4":          oracle_cf_reach,
}


def make_oracle_cf_fn(
    env_name: str,
) -> Callable[..., Optional[List[Counterfactual]]]:
    """Return the oracle CF callback for a specific env.

    Signature matches CounterfactualHERBuffer with cf_input_kind='state':

        fn(trajectory=dict) -> Optional[List[Counterfactual]]
    """
    if env_name not in _ORACLE_REGISTRY:
        raise ValueError(
            f"No oracle CF for env '{env_name}'. "
            f"Known: {list(_ORACLE_REGISTRY.keys())}"
        )
    oracle = _ORACLE_REGISTRY[env_name]

    def oracle_cf_fn(trajectory: Dict[str, Any], **kwargs) -> Optional[List[Counterfactual]]:
        try:
            return oracle(trajectory)
        except Exception as e:
            logger.warning(f"[oracle_cf:{env_name}] failure: {e}")
            return None

    return oracle_cf_fn
