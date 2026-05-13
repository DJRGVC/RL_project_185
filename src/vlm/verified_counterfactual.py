"""
VerifiedCounterfactualLocalizer — physics-grounded counterfactual hindsight.

Path N1 (novel direction). Closes the teleport-collapse failure mode that
agent C1's analysis surfaced: when GPT-4o / Claude is asked
"what position should the object have reached?" it frequently outputs
`corrective_position == desired_goal` — a magical teleport.  C1's adapter
papers over this with a 5cm gate; this module replaces the gate with a
mechanism: ask the VLM for a corrective ACTION SEQUENCE, then execute it in
a fresh fork of the simulator from the failure state and check whether the
goal is reached.  Verified counterfactuals carry confidence 1.0 by
construction (the env's own sparse reward signed off); unverified ones are
rejected.

Design / interface contract
---------------------------
- Wraps an existing C1-style `CounterfactualLocalizer.localize(...)` callable.
  We do not import the C1 file (it lives on a sibling worktree); instead we
  accept a `vlm_fn` whose signature is dict-in / dict-out and matches the
  schema in `agent_reports/C1_counterfactual_outputs.json`.
- Owns a fresh "verifier" Gymnasium-Robotics env (same env_name as the
  rollout) and a state-snapshot helper.
- Verification protocol (per failed episode):
    1. Localize the failure timestep K (delegated to C1's localizer or the
       supplied `failure_t`).
    2. Snapshot the world at K from the *original* episode's state buffer
       (passed in via `episode_states`, a list of qpos/qvel/mocap/goal tuples).
    3. Reset the verifier env to that snapshot.
    4. Pull the VLM's `corrective_action` 4-vector (clipped to the env
       action space) and execute it for `n_verify_steps` (default 50 —
       roughly the remaining horizon of a Fetch episode).
    5. If `compute_reward(achieved_goal, desired_goal) >= 0` (i.e., the
       sparse reward fires) at any point in the rollout, mark the
       counterfactual VERIFIED.
- Returns a `VerifiedCounterfactual` record per episode containing the
  verified trajectory (or None) and provenance for downstream
  hindsight relabeling.

Why this is novel relative to Sharony 2602.01915 and C2's stub
--------------------------------------------------------------
- Sharony reweights *real* transitions with a VLM-derived priority score.
- C2's CF-HER stub relabels with a VLM-imagined goal position, *trusting
  the VLM*.  When the VLM teleports, C2 either feeds bogus goals into the
  buffer or has to hand-gate them.
- This module relabels with a VLM-imagined *action sequence* and only
  trusts it if a frozen simulator confirms it would have succeeded.
  The trust comes from physics, not from the VLM's self-reported
  confidence.

Connection to model-based RL
----------------------------
The verifier env is, formally, an offline rollout under a perfect
ground-truth world model — the same env class as training.  Compared to
MuZero-style learned-model search, the search policy is "execute the
VLM's suggestion" (1 trajectory, no tree), and the model is the
ground-truth simulator (no learned dynamics error).  This is closer to
**model-predictive control with a language prior** than to learned-model
planning: we do not search; we verify.

Implementation notes
--------------------
- Fetch envs are MuJoCo + a freejoint object + mocap-driven end-effector.
  State snapshot must include qpos, qvel, data.time, mocap_pos,
  mocap_quat, and the goal vector (`env.unwrapped.goal`).  After writing
  these back, `mujoco.mj_forward(model, data)` propagates the kinematic
  derived quantities; `step()` then re-enters the integrator cleanly.
- ~150–250 LOC budget. This is design + smoke only; no buffer wiring.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Public types
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class MujocoSnapshot:
    """Frozen MuJoCo state at a single timestep — everything needed to step."""
    qpos: np.ndarray
    qvel: np.ndarray
    time: float
    mocap_pos: np.ndarray
    mocap_quat: np.ndarray
    goal: np.ndarray


@dataclass
class VerifiedCounterfactual:
    """Output record. `verified=True` means the rollout succeeded."""
    failure_t: int
    desired_goal: np.ndarray
    achieved_at_failure: np.ndarray
    corrective_action: Optional[np.ndarray]
    corrective_explanation: str
    vlm_confidence: float
    verified: bool
    verified_at_step: Optional[int]
    verified_achieved_goal: Optional[np.ndarray]
    final_distance: float
    rejection_reason: Optional[str]
    # Trajectory of (achieved_goal, action) during verification rollout.
    rollout_achieved: List[np.ndarray] = field(default_factory=list)
    rollout_actions: List[np.ndarray] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = self.__dict__.copy()
        for k, v in list(d.items()):
            if isinstance(v, np.ndarray):
                d[k] = v.tolist()
            elif isinstance(v, list) and v and isinstance(v[0], np.ndarray):
                d[k] = [arr.tolist() for arr in v]
        return d


# ─────────────────────────────────────────────────────────────────────────────
# Verifier
# ─────────────────────────────────────────────────────────────────────────────


class VerifiedCounterfactualLocalizer:
    """Wraps a VLM counterfactual generator with simulator-grounded verification.

    Parameters
    ----------
    env_name:
        Gymnasium-Robotics env id (e.g., 'FetchPush-v4'). A *fresh* env is
        constructed internally for verification rollouts — never the
        training env, to avoid disturbing the learner's RNG / state.
    vlm_fn:
        Callable(achieved_goals, desired_goal, keyframes, failure_t,
                 task_description) -> dict with keys
        {corrective_action, corrective_position, confidence, explanation}.
        If None, the wrapper expects pre-computed VLM outputs to be passed
        directly into `verify()`.
    n_verify_steps:
        Maximum simulator steps in the verification rollout. Default 50
        matches the Fetch default horizon.
    success_threshold:
        Distance below which we declare the rollout successful. Fetch envs
        use 0.05 (5 cm); we expose it as a parameter for downstream
        environments.
    repeat_action:
        If the VLM returns a single action vector, we repeat it for the
        full rollout. This is the minimal interface — future versions
        could ask the VLM for an action sequence.
    """

    def __init__(
        self,
        env_name: str,
        vlm_fn: Optional[Callable[..., Dict[str, Any]]] = None,
        n_verify_steps: int = 50,
        success_threshold: float = 0.05,
        repeat_action: bool = True,
    ):
        self.env_name          = env_name
        self.vlm_fn            = vlm_fn
        self.n_verify_steps    = int(n_verify_steps)
        self.success_threshold = float(success_threshold)
        self.repeat_action     = bool(repeat_action)
        self._env              = None
        self._mujoco           = None

        self.stats: Dict[str, int] = {
            "verifications_attempted": 0,
            "verifications_succeeded": 0,
            "rejected_teleport":       0,
            "rejected_no_action":      0,
            "rejected_no_success":     0,
            "rejected_exception":      0,
        }

    # ── env / snapshot machinery ───────────────────────────────────────────

    def _ensure_env(self):
        if self._env is None:
            import gymnasium as gym
            import gymnasium_robotics  # noqa: F401 — registers envs
            import mujoco
            self._mujoco = mujoco
            # render_mode=None: we don't need pixels during verification.
            self._env = gym.make(self.env_name, render_mode=None)
            self._env.reset(seed=0)
        return self._env

    @staticmethod
    def snapshot_from_env(env) -> MujocoSnapshot:
        """Capture a full state snapshot from a *running* env. Use this on
        the *training* env at timestep K to feed `verify()`."""
        unw = env.unwrapped
        return MujocoSnapshot(
            qpos      = unw.data.qpos.copy(),
            qvel      = unw.data.qvel.copy(),
            time      = float(unw.data.time),
            mocap_pos = unw.data.mocap_pos.copy(),
            mocap_quat= unw.data.mocap_quat.copy(),
            goal      = np.asarray(unw.goal, dtype=np.float64).copy(),
        )

    def _restore(self, env, snap: MujocoSnapshot) -> None:
        """Write a snapshot back into the verifier env and re-derive kinematics."""
        unw = env.unwrapped
        unw.data.qpos[:]      = snap.qpos
        unw.data.qvel[:]      = snap.qvel
        unw.data.time         = snap.time
        unw.data.mocap_pos[:] = snap.mocap_pos
        unw.data.mocap_quat[:]= snap.mocap_quat
        # The goal lives outside MuJoCo state. Fetch envs read `unw.goal`
        # inside `_get_obs` and `compute_reward`.
        unw.goal = snap.goal.copy()
        # mj_forward propagates xpos/xquat/site_xpos from qpos.
        self._mujoco.mj_forward(unw.model, unw.data)

    # ── verification ───────────────────────────────────────────────────────

    def verify(
        self,
        snap: MujocoSnapshot,
        corrective_action: Optional[np.ndarray],
        vlm_explanation: str = "",
        vlm_confidence: float = 0.0,
        action_sequence: Optional[List[np.ndarray]] = None,
        failure_t: int = -1,
        achieved_at_failure: Optional[np.ndarray] = None,
    ) -> VerifiedCounterfactual:
        """Execute the VLM's corrective action from the snapshot and verify.

        Args:
            snap: state at failure timestep K (e.g., from snapshot_from_env).
            corrective_action: single 4-vector to repeat (Fetch action shape).
            action_sequence: alternative — a list of action 4-vectors to play.
            failure_t: index for bookkeeping.
            achieved_at_failure: object position at K, for the record.
        Returns:
            VerifiedCounterfactual record. `verified=False` indicates the
            counterfactual must be rejected; teleport-collapse instructions
            cannot pass this gate because there is no 4-vector that
            instantly relocates a block 50 cm.
        """
        self.stats["verifications_attempted"] += 1
        env = self._ensure_env()
        result = VerifiedCounterfactual(
            failure_t           = failure_t,
            desired_goal        = snap.goal.astype(np.float32),
            achieved_at_failure = (
                np.asarray(achieved_at_failure, dtype=np.float32)
                if achieved_at_failure is not None
                else np.zeros(3, dtype=np.float32)
            ),
            corrective_action      = None,
            corrective_explanation = vlm_explanation,
            vlm_confidence         = float(vlm_confidence),
            verified               = False,
            verified_at_step       = None,
            verified_achieved_goal = None,
            final_distance         = float("nan"),
            rejection_reason       = None,
        )

        # Build action plan.
        if action_sequence is not None:
            seq = [np.asarray(a, dtype=np.float32) for a in action_sequence]
            result.corrective_action = seq[0] if seq else None
        elif corrective_action is not None:
            a = np.asarray(corrective_action, dtype=np.float32)
            result.corrective_action = a
            seq = [a.copy() for _ in range(self.n_verify_steps)] if self.repeat_action else [a]
        else:
            self.stats["rejected_no_action"] += 1
            result.rejection_reason = "no_corrective_action_provided"
            return result

        # Clip to action bounds for safety. Fetch action_space is Box([-1,1], shape=(4,)).
        low  = np.asarray(env.action_space.low, dtype=np.float32)
        high = np.asarray(env.action_space.high, dtype=np.float32)
        seq = [np.clip(a, low, high) for a in seq]

        # Reset verifier env state to the failure timestep.
        try:
            env.reset()
            self._restore(env, snap)
        except Exception as e:
            self.stats["rejected_exception"] += 1
            result.rejection_reason = f"restore_failed: {e!r}"
            return result

        # Roll out.
        best_dist = float("inf")
        try:
            for step in range(self.n_verify_steps):
                a = seq[min(step, len(seq) - 1)]
                obs, _r, terminated, truncated, info = env.step(a)
                # In gymnasium goal envs, obs is a dict.
                if isinstance(obs, dict):
                    ag = np.asarray(obs["achieved_goal"], dtype=np.float32)
                    dg = np.asarray(obs["desired_goal"],  dtype=np.float32)
                else:
                    # Flat obs: pull from env.unwrapped (defensive — depends on wrapping).
                    inner = env.unwrapped._get_obs()
                    ag = np.asarray(inner["achieved_goal"], dtype=np.float32)
                    dg = np.asarray(inner["desired_goal"],  dtype=np.float32)

                result.rollout_achieved.append(ag)
                result.rollout_actions.append(a.astype(np.float32))

                d = float(np.linalg.norm(ag - dg))
                if d < best_dist:
                    best_dist = d

                # Use the env's own compute_reward — this is the headline:
                # the simulator declares success, not our heuristic.
                rew = float(env.unwrapped.compute_reward(ag, dg, info))
                # Sparse Fetch reward: -1 (fail) or 0 (success). Treat 0 (or
                # better) as verified.
                if rew >= -1e-6:
                    result.verified               = True
                    result.verified_at_step       = step
                    result.verified_achieved_goal = ag.copy()
                    result.final_distance         = d
                    self.stats["verifications_succeeded"] += 1
                    return result

                if terminated or truncated:
                    break

        except Exception as e:
            self.stats["rejected_exception"] += 1
            result.rejection_reason = f"rollout_exception: {e!r}"
            result.final_distance = best_dist
            return result

        result.final_distance = best_dist
        self.stats["rejected_no_success"] += 1
        result.rejection_reason = f"goal_not_reached (best_dist={best_dist:.3f})"
        return result

    # ── high-level entry: generate + verify ────────────────────────────────

    def localize_and_verify(
        self,
        snap: MujocoSnapshot,
        achieved_goals: np.ndarray,
        desired_goal: np.ndarray,
        keyframes: Optional[List[np.ndarray]] = None,
        failure_t: int = -1,
        task_description: str = "",
        achieved_at_failure: Optional[np.ndarray] = None,
    ) -> VerifiedCounterfactual:
        """Convenience: call self.vlm_fn(...) then verify(). Use this when a
        live VLM is wired in. For offline smoke testing, call `verify()`
        directly with precomputed VLM outputs."""
        if self.vlm_fn is None:
            raise RuntimeError(
                "VerifiedCounterfactualLocalizer.vlm_fn not configured; "
                "either pass vlm_fn at construction or call .verify() with "
                "precomputed VLM outputs."
            )
        out = self.vlm_fn(
            achieved_goals   = achieved_goals,
            desired_goal     = desired_goal,
            keyframes        = keyframes,
            failure_t        = failure_t,
            task_description = task_description,
        )
        action = out.get("corrective_action") if isinstance(out, dict) else None
        # Teleport-collapse: VLM returns a position equal to the goal and
        # no action. We don't even bother running the simulator.
        if action is None:
            self.stats["rejected_teleport"] += 1
            return VerifiedCounterfactual(
                failure_t           = failure_t,
                desired_goal        = np.asarray(desired_goal, dtype=np.float32),
                achieved_at_failure = (
                    np.asarray(achieved_at_failure, dtype=np.float32)
                    if achieved_at_failure is not None
                    else np.zeros(3, dtype=np.float32)
                ),
                corrective_action      = None,
                corrective_explanation = str(out.get("explanation", "")) if isinstance(out, dict) else "",
                vlm_confidence         = float(out.get("confidence", 0.0)) if isinstance(out, dict) else 0.0,
                verified               = False,
                verified_at_step       = None,
                verified_achieved_goal = None,
                final_distance         = float("nan"),
                rejection_reason       = "vlm_returned_no_action_only_position",
            )

        return self.verify(
            snap                = snap,
            corrective_action   = np.asarray(action, dtype=np.float32),
            vlm_explanation     = str(out.get("explanation", "")) if isinstance(out, dict) else "",
            vlm_confidence      = float(out.get("confidence", 0.0)) if isinstance(out, dict) else 0.0,
            failure_t           = failure_t,
            achieved_at_failure = achieved_at_failure,
        )

    # ── diagnostics ────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, int]:
        return dict(self.stats)


# ─────────────────────────────────────────────────────────────────────────────
# Smoke-test helpers
# ─────────────────────────────────────────────────────────────────────────────


def reconstruct_snapshot_for_synthetic_episode(
    env_name: str,
    seed: int,
    achieved_at_failure: np.ndarray,
    desired_goal: np.ndarray,
    failure_t: int,
) -> MujocoSnapshot:
    """For smoke-only: construct a plausible MuJoCo snapshot at the failure
    timestep by re-rolling out the same seed and then *placing* the object
    at `achieved_at_failure`.

    Real training would call `snapshot_from_env` on the live training env
    at step K. C1's existing JSON does not record qpos/qvel, so for the
    3-episode smoke we approximate by:
      1. Resetting the env with the original seed (recovers initial robot
         pose).
      2. Writing the object's freejoint qpos to `achieved_at_failure` and
         zeroing its velocity.
      3. Writing the goal in `unw.goal`.

    The resulting snapshot is *kinematically consistent* with the failure
    state we want to recover, even though the robot pose is the initial
    one rather than the precise mid-episode pose. For verifying whether a
    corrective ACTION can reach the goal from "block at failure position",
    this is good enough — the dynamics from that state under the
    corrective action is what we want to test.
    """
    import gymnasium as gym
    import gymnasium_robotics  # noqa: F401
    import mujoco

    env = gym.make(env_name, render_mode=None)
    env.reset(seed=seed)
    unw = env.unwrapped

    # Locate the object freejoint (qpos slot). FetchPush/PickAndPlace use
    # "object0:joint" as a 7-DOF freejoint (x,y,z,qw,qx,qy,qz).
    obj_joint_name = "object0:joint"
    obj_joint_id = mujoco.mj_name2id(
        unw.model, mujoco.mjtObj.mjOBJ_JOINT, obj_joint_name
    )
    if obj_joint_id < 0:
        raise RuntimeError(f"Joint {obj_joint_name} not found in {env_name}")
    qpos_addr = unw.model.jnt_qposadr[obj_joint_id]
    qvel_addr = unw.model.jnt_dofadr[obj_joint_id]

    # Write the achieved position into the freejoint qpos (rotation = identity).
    unw.data.qpos[qpos_addr : qpos_addr + 3] = np.asarray(
        achieved_at_failure, dtype=np.float64
    )
    unw.data.qpos[qpos_addr + 3 : qpos_addr + 7] = np.array(
        [1.0, 0.0, 0.0, 0.0], dtype=np.float64
    )
    unw.data.qvel[qvel_addr : qvel_addr + 6] = 0.0
    unw.goal = np.asarray(desired_goal, dtype=np.float64).copy()
    mujoco.mj_forward(unw.model, unw.data)

    snap = VerifiedCounterfactualLocalizer.snapshot_from_env(env)
    env.close()
    return snap
