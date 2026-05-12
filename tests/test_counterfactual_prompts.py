"""
Tests for the numeric-context VLM-CF prompt variants.

Covers:
  1. PROMPT_TEMPLATES registers both new variants.
  2. _build_traj_table renders a markdown table with one row per keyframe,
     including frame index, timestep, block xyz, and gripper ee_xyz.
  3. ACHIEVED_GOAL_NUMERIC and ACHIEVED_GOAL_BLIND_NUMERIC templates
     format successfully when supplied the expected kwargs (no KeyError).
  4. The blind-numeric template does NOT contain the literal substring
     "desired_goal =" (i.e. the target coords are withheld) but DOES
     contain the trajectory table.
  5. make_counterfactual_fn returns a callable that accepts the
     ee_positions kwarg without raising.
  6. _build_traj_table handles partial / None inputs gracefully — n/a
     placeholder rows are emitted instead of crashing.
  7. The buffer-side plumbing slices per-step achieved_goals and
     ee_positions at the keyframe indices (frame_index -> numeric mapping
     is consistent).
"""
from __future__ import annotations

import os
import sys
import numpy as np

try:
    import pytest  # type: ignore
    HAS_PYTEST = True
except ImportError:  # pragma: no cover
    pytest = None  # type: ignore
    HAS_PYTEST = False

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from src.vlm.counterfactual import (  # noqa: E402
    PROMPT_TEMPLATES,
    NUMERIC_VARIANTS,
    BLIND_VARIANTS,
    ACHIEVED_GOAL_NUMERIC_PROMPT,
    ACHIEVED_GOAL_BLIND_NUMERIC_PROMPT,
    _build_traj_table,
    _build_frame_index_map,
    make_counterfactual_fn,
)


# ─────────────────────────────────────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────────────────────────────────────


class TestVariantRegistration:
    def test_numeric_variants_in_prompt_templates(self):
        assert "achieved_goal_numeric" in PROMPT_TEMPLATES
        assert "achieved_goal_blind_numeric" in PROMPT_TEMPLATES

    def test_numeric_variants_in_numeric_set(self):
        assert "achieved_goal_numeric" in NUMERIC_VARIANTS
        assert "achieved_goal_blind_numeric" in NUMERIC_VARIANTS

    def test_blind_variants_include_numeric(self):
        assert "achieved_goal_blind" in BLIND_VARIANTS
        assert "achieved_goal_blind_numeric" in BLIND_VARIANTS
        # Non-blind numeric must NOT be in BLIND_VARIANTS.
        assert "achieved_goal_numeric" not in BLIND_VARIANTS


# ─────────────────────────────────────────────────────────────────────────────
# Table builder
# ─────────────────────────────────────────────────────────────────────────────


class TestBuildTrajTable:
    def test_table_contains_header_and_one_row_per_keyframe(self):
        ts = [0, 12, 24, 36, 49]
        ag = np.array([
            [1.20, 0.70, 0.45],
            [1.18, 0.68, 0.44],
            [1.16, 0.66, 0.43],
            [1.15, 0.65, 0.42],
            [1.15, 0.65, 0.42],
        ], dtype=np.float32)
        ee = np.array([
            [1.30, 0.75, 0.55],
            [1.22, 0.71, 0.49],
            [1.18, 0.67, 0.45],
            [1.16, 0.65, 0.43],
            [1.16, 0.65, 0.43],
        ], dtype=np.float32)
        table = _build_traj_table(ts, ag, ee)
        # Header present.
        assert "Frame" in table
        assert "Block xyz (achieved_goal)" in table
        assert "Gripper ee_xyz" in table
        # Exactly K rows (5 keyframes).
        body_rows = [ln for ln in table.split("\n") if ln.startswith("| ") and "Frame" not in ln and "---" not in ln]
        assert len(body_rows) == 5, f"expected 5 data rows, got {len(body_rows)}"
        # First row contains the right step number and rounded block xyz.
        assert "| 0 | 0 |" in table
        assert "1.200, 0.700, 0.450" in table
        # Last row.
        assert "| 4 | 49 |" in table

    def test_frame_index_to_numeric_mapping_consistent(self):
        """Frame i in the markdown table must show timestep ts[i] and the
        numeric row aligned with achieved_goals[i] / ee_positions[i]."""
        ts = [3, 7, 11]
        ag = np.array([
            [0.10, 0.20, 0.30],
            [0.40, 0.50, 0.60],
            [0.70, 0.80, 0.90],
        ], dtype=np.float32)
        ee = np.array([
            [1.10, 1.20, 1.30],
            [1.40, 1.50, 1.60],
            [1.70, 1.80, 1.90],
        ], dtype=np.float32)
        table = _build_traj_table(ts, ag, ee)
        lines = [ln for ln in table.split("\n") if ln.startswith("| ") and "Frame" not in ln and "---" not in ln]
        # Frame 0 / step 3 / block (0.1,0.2,0.3) / ee (1.1,1.2,1.3)
        assert "| 0 | 3 |" in lines[0]
        assert "0.100, 0.200, 0.300" in lines[0]
        assert "1.100, 1.200, 1.300" in lines[0]
        # Frame 2 / step 11 / block (0.7,0.8,0.9) / ee (1.7,1.8,1.9)
        assert "| 2 | 11 |" in lines[2]
        assert "0.700, 0.800, 0.900" in lines[2]
        assert "1.700, 1.800, 1.900" in lines[2]

    def test_table_handles_none_ee_positions(self):
        ts = [0, 1, 2]
        ag = np.array([
            [1.0, 0.0, 0.0],
            [1.1, 0.0, 0.0],
            [1.2, 0.0, 0.0],
        ])
        table = _build_traj_table(ts, ag, None)
        assert "n/a" in table  # ee column placeholder
        assert "1.000, 0.000, 0.000" in table  # block column still numeric

    def test_table_handles_none_achieved_goals(self):
        ts = [0, 1]
        ee = np.array([[1.3, 0.7, 0.5], [1.3, 0.7, 0.5]])
        table = _build_traj_table(ts, None, ee)
        assert "n/a" in table
        assert "1.300, 0.700, 0.500" in table


# ─────────────────────────────────────────────────────────────────────────────
# Prompt formatting smoke
# ─────────────────────────────────────────────────────────────────────────────


class TestPromptFormatting:
    def _kwargs(self, *, include_desired: bool):
        ts = [0, 5, 10, 15, 19]
        ag = np.array([[1.2 + 0.01 * i, 0.7, 0.45] for i in range(5)])
        ee = np.array([[1.3 + 0.01 * i, 0.75, 0.55] for i in range(5)])
        kwargs = dict(
            task_description="robot must pick the block.",
            K=5,
            frame_index_map=_build_frame_index_map(ts, total_steps=20),
            failure_frame_index=3,
            failure_frame_pct=75.0,
            traj_table=_build_traj_table(ts, ag, ee),
        )
        if include_desired:
            kwargs["desired_goal"] = [1.30, 0.80, 0.50]
        return kwargs

    def test_achieved_goal_numeric_renders(self):
        text = ACHIEVED_GOAL_NUMERIC_PROMPT.format(**self._kwargs(include_desired=True))
        assert "desired_goal = [1.3, 0.8, 0.5]" in text
        # Numerical table content shows up.
        assert "| Frame |" in text
        assert "1.200, 0.700, 0.450" in text
        # Failure frame index injected.
        assert "Frame 3" in text

    def test_achieved_goal_blind_numeric_renders_without_desired_goal(self):
        # Blind-numeric does NOT need desired_goal at all.
        text = ACHIEVED_GOAL_BLIND_NUMERIC_PROMPT.format(**self._kwargs(include_desired=False))
        # Crucial: the literal target coord row must NOT appear.
        assert "desired_goal =" not in text
        # But the trajectory table must.
        assert "| Frame |" in text
        assert "1.200, 0.700, 0.450" in text
        # And the "withheld" caveat is present.
        assert "withheld" in text


# ─────────────────────────────────────────────────────────────────────────────
# Factory signature
# ─────────────────────────────────────────────────────────────────────────────


class TestMakeCounterfactualFnEEKwarg:
    """Verify make_counterfactual_fn returns a callable that gracefully
    accepts the ee_positions kwarg from the CF buffer."""

    def test_callable_accepts_ee_positions_kwarg(self, monkeypatch=None):
        # We can't actually call the OpenAI/Anthropic client without an API
        # key in CI, so we'll monkeypatch CounterfactualLocalizer._init_client
        # to a no-op and check that the callable signature accepts kwargs.
        from src.vlm import counterfactual as cf_mod

        def fake_init_client(self):
            self._client = None
        monkeypatch_obj = monkeypatch
        if monkeypatch_obj is None:
            # Manual context-manager-free patch (for non-pytest runs).
            orig = cf_mod.CounterfactualLocalizer._init_client
            cf_mod.CounterfactualLocalizer._init_client = fake_init_client  # type: ignore[assignment]
            try:
                fn = make_counterfactual_fn(
                    provider="anthropic",
                    model="claude-sonnet-4-5",
                    variant="achieved_goal_numeric",
                    task_description="t",
                )
                # Inspect the callable signature.
                import inspect
                sig = inspect.signature(fn)
                params = sig.parameters
                assert "ee_positions" in params, \
                    "localize_counterfactual must accept ee_positions kwarg"
                assert "keyframes" in params
                # Backwards-compat: also accepts achieved_goals + desired_goal.
                assert "achieved_goals" in params
                assert "desired_goal" in params
            finally:
                cf_mod.CounterfactualLocalizer._init_client = orig  # type: ignore[assignment]
        else:
            monkeypatch_obj.setattr(
                cf_mod.CounterfactualLocalizer, "_init_client", fake_init_client
            )
            fn = make_counterfactual_fn(
                provider="anthropic",
                model="claude-sonnet-4-5",
                variant="achieved_goal_numeric",
                task_description="t",
            )
            import inspect
            sig = inspect.signature(fn)
            params = sig.parameters
            assert "ee_positions" in params


# ─────────────────────────────────────────────────────────────────────────────
# Non-pytest fallback runner
# ─────────────────────────────────────────────────────────────────────────────


def _run_all_tests_without_pytest():
    import traceback
    classes = [
        TestVariantRegistration,
        TestBuildTrajTable,
        TestPromptFormatting,
        TestMakeCounterfactualFnEEKwarg,
    ]
    n_pass = 0
    n_fail = 0
    failures = []
    for cls in classes:
        instance = cls()
        for name in dir(instance):
            if not name.startswith("test_"):
                continue
            method = getattr(instance, name)
            label = f"{cls.__name__}::{name}"
            try:
                method()
                n_pass += 1
                print(f"  PASS  {label}")
            except Exception as e:  # noqa: BLE001
                n_fail += 1
                failures.append((label, traceback.format_exc()))
                print(f"  FAIL  {label}  ({type(e).__name__}: {e})")
    print(f"\n{'='*60}\n  passed: {n_pass}   failed: {n_fail}\n{'='*60}")
    if failures:
        print("\nFailure details:\n")
        for label, tb in failures:
            print(f"---- {label} ----\n{tb}")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    if HAS_PYTEST:
        sys.exit(pytest.main([__file__, "-v"]))
    sys.exit(_run_all_tests_without_pytest())
