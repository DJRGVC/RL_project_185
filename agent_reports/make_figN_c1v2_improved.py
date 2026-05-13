"""Improved NeurIPS-style figure for figN_c1v2_real_vs_synthetic.

Key improvements over the original (agent-a7a36bbf8575e1685/scripts/make_c1v2_figure.py):
  1. Removed bar value labels — axes already show the scale; labels clutter and
     violate NeurIPS guideline "No value labels on bars unless axes can't show".
  2. Fixed figure width: 6.75 in (NeurIPS two-column) instead of 8.6 in.
  3. Horizontal gridlines only — original had grid=True globally but then
     called grid(axis="x", visible=False) inconsistently; made explicit.
  4. Slightly taller per-panel to compensate for the narrower total width
     (2.8 → 3.1) so bars don't look compressed.

Reads:
    agent_reports/C1_counterfactual_outputs.json   (C1 synthetic, Opus 4.7)
    agent_reports/C1v2_real_data_outputs.json      (C1v2 real, multiple models)

Output:
    agent_reports/figs/figN_c1v2_real_vs_synthetic.png  (overwritten)
    agent_reports/figs/figN_c1v2_real_vs_synthetic.pdf  (overwritten)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

# ── NeurIPS rcParams ─────────────────────────────────────────────────────────
mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "legend.frameon": False,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": "#dddddd",
    "grid.linewidth": 0.5,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

# Colour-blind safe palette (Tableau Color Blind 10)
CB = {
    "synthetic":   "#ABABAB",   # neutral gray
    "real_opus":   "#FF800E",   # orange
    "real_sonnet": "#006BA4",   # blue
}

VARIANTS = ["narrative", "action", "achieved_goal", "all"]
METRICS = ["plausibility", "specificity"]
TELEPORT_RADIUS_M = 0.05
TELEPORT_VARIANTS = ("achieved_goal", "all")

REPO = Path(__file__).resolve().parents[1]
SYNTH_PATH = REPO / "agent_reports" / "C1_counterfactual_outputs.json"
REAL_PATH  = REPO / "agent_reports" / "C1v2_real_data_outputs.json"


# ── helpers ──────────────────────────────────────────────────────────────────

def _safe_float(v) -> Optional[float]:
    try:
        f = float(v)
        return None if np.isnan(f) else f
    except (TypeError, ValueError):
        return None


def aggregate_synthetic(path: Path) -> Dict[str, Dict[str, Tuple[float, float, int]]]:
    if not path.exists():
        return {}
    d = json.loads(path.read_text())
    by_v: Dict[str, Dict[str, List[float]]] = {v: {m: [] for m in METRICS} for v in VARIANTS}
    for ep in d["episodes"]:
        for v, item in ep.get("variants", {}).items():
            if v not in by_v:
                continue
            judge = item.get("judge") or {}
            for m in METRICS:
                val = _safe_float(judge.get(m))
                if val is not None:
                    by_v[v][m].append(val)
    out: Dict[str, Dict[str, Tuple[float, float, int]]] = {}
    for v, mp in by_v.items():
        out[v] = {}
        for m, lst in mp.items():
            if lst:
                mean = float(np.mean(lst))
                sem = float(np.std(lst, ddof=1) / np.sqrt(len(lst))) if len(lst) > 1 else 0.0
                out[v][m] = (mean, sem, len(lst))
            else:
                out[v][m] = (np.nan, 0.0, 0)
    return out


def aggregate_real(path: Path) -> Dict[str, Dict[str, Dict[str, Tuple[float, float, int]]]]:
    if not path.exists():
        return {}
    d = json.loads(path.read_text())
    by_model: Dict[str, Dict[str, Dict[str, List[float]]]] = {}
    for ep in d["episodes"]:
        for slot, prov in ep.get("providers", {}).items():
            model = prov.get("model", slot.split(":", 1)[-1])
            by_model.setdefault(model, {v: {m: [] for m in METRICS} for v in VARIANTS})
            for v, item in prov.get("variants", {}).items():
                if v not in VARIANTS:
                    continue
                judge = item.get("judge") or {}
                for m in METRICS:
                    val = _safe_float(judge.get(m))
                    if val is not None:
                        by_model[model][v][m].append(val)
    out: Dict[str, Dict[str, Dict[str, Tuple[float, float, int]]]] = {}
    for model, mp in by_model.items():
        out[model] = {}
        for v, vmp in mp.items():
            out[model][v] = {}
            for m, lst in vmp.items():
                if lst:
                    mean = float(np.mean(lst))
                    sem = float(np.std(lst, ddof=1) / np.sqrt(len(lst))) if len(lst) > 1 else 0.0
                    out[model][v][m] = (mean, sem, len(lst))
                else:
                    out[model][v][m] = (np.nan, 0.0, 0)
    return out


def teleport_rate_synthetic(path: Path) -> Dict[str, Tuple[float, int]]:
    if not path.exists():
        return {}
    d = json.loads(path.read_text())
    rates: Dict[str, list] = {v: [] for v in TELEPORT_VARIANTS}
    for ep in d["episodes"]:
        dg = ep.get("desired_goal")
        if dg is None:
            continue
        for v in TELEPORT_VARIANTS:
            item = ep.get("variants", {}).get(v)
            if not item or item.get("parse_error") is not None:
                continue
            pos = item.get("corrective_position")
            if pos is None:
                continue
            rates[v].append(int(np.linalg.norm(np.asarray(pos) - np.asarray(dg)) < TELEPORT_RADIUS_M))
    return {v: (float(np.mean(lst)) if lst else np.nan, len(lst)) for v, lst in rates.items()}


def teleport_rate_real(path: Path) -> Dict[str, Dict[str, Tuple[float, int]]]:
    if not path.exists():
        return {}
    d = json.loads(path.read_text())
    rates: Dict[str, Dict[str, list]] = {}
    for ep in d["episodes"]:
        for slot, prov in ep.get("providers", {}).items():
            if "variants" not in prov:
                continue
            model = prov.get("model", slot.split(":", 1)[-1])
            dg = prov.get("desired_goal")
            if dg is None:
                continue
            rates.setdefault(model, {v: [] for v in TELEPORT_VARIANTS})
            for v in TELEPORT_VARIANTS:
                item = prov["variants"].get(v)
                if not item or item.get("parse_error") is not None:
                    continue
                pos = item.get("corrective_position")
                if pos is None:
                    continue
                rates[model][v].append(int(np.linalg.norm(np.asarray(pos) - np.asarray(dg)) < TELEPORT_RADIUS_M))
    return {
        model: {v: (float(np.mean(lst)) if lst else np.nan, len(lst)) for v, lst in mp.items()}
        for model, mp in rates.items()
    }


# ── figure ───────────────────────────────────────────────────────────────────

def make_figure(
    synth: Dict[str, Any],
    real: Dict[str, Any],
    teleport_synth: Dict[str, Tuple[float, int]],
    teleport_real: Dict[str, Dict[str, Tuple[float, int]]],
    out_path: Path,
) -> None:
    """Three-panel figure: (a) plausibility, (b) specificity, (c) teleport-collapse.

    Improvements vs. original:
      - No bar value labels (removed; axes already convey the information).
      - 6.75" width (NeurIPS two-column), not 8.6".
      - Horizontal gridlines only (explicit axis="y" on all panels).
    """
    # Model order: Opus first, then Sonnet
    model_order: List[str] = []
    for preferred in ("claude-opus-4-7", "claude-sonnet-4-5"):
        if preferred in real:
            model_order.append(preferred)
    for m in real:
        if m not in model_order:
            model_order.append(m)

    # ── layout ───────────────────────────────────────────────────────────
    # 6.75" × 3.1" — NeurIPS two-column width; slightly taller than the
    # 8.6"×2.8 original to keep bar aspect ratios sane.
    fig, axes = plt.subplots(1, 3, figsize=(6.75, 3.1))

    x = np.arange(len(VARIANTS))
    x_tele = np.arange(len(TELEPORT_VARIANTS))
    n_hues = 1 + len(model_order)
    bar_w_full = 0.78 / n_hues
    bar_w_tele = 0.65 / n_hues

    def _hue_kwargs(label: str) -> Dict[str, Any]:
        if label == "synthetic":
            return {"color": CB["synthetic"], "label": "C1 synthetic (Opus 4.7)"}
        if "opus" in label:
            return {"color": CB["real_opus"], "label": "C1v2 real (Opus 4.7)"}
        return {"color": CB["real_sonnet"], "label": "C1v2 real (Sonnet 4.5)"}

    cap_kw = dict(elinewidth=0.7, capsize=2.0, capthick=0.7, ecolor="#333333")

    # ── panels 1 & 2: plausibility / specificity ─────────────────────────
    for ax_idx, metric in enumerate(METRICS):
        ax = axes[ax_idx]
        hues = [("synthetic", None)] + [("real", m) for m in model_order]
        for h_idx, (kind, model) in enumerate(hues):
            offset = (h_idx - (n_hues - 1) / 2) * bar_w_full
            means, sems = [], []
            for v in VARIANTS:
                if kind == "synthetic":
                    bucket = synth.get(v, {}).get(metric)
                else:
                    bucket = real.get(model, {}).get(v, {}).get(metric)
                if bucket is None:
                    means.append(np.nan); sems.append(0.0)
                else:
                    means.append(bucket[0]); sems.append(bucket[1])

            color_label = (
                "synthetic" if kind == "synthetic"
                else ("real_opus" if "opus" in (model or "") else "real_sonnet")
            )
            kw = _hue_kwargs(color_label)
            ax.bar(
                x + offset, means, bar_w_full, yerr=sems,
                edgecolor="white", linewidth=0.4,
                error_kw=cap_kw,
                **kw,
            )
            # NO bar value labels — axes already show the scale.

        ax.set_xticks(x)
        # Use short labels to avoid crowding: "narr.", "action", "ag", "all"
        SHORT_LABELS = ["narr.", "action", "ag", "all"]
        ax.set_xticklabels(SHORT_LABELS, rotation=0, ha="center")
        ax.set_ylim(0, 1.05)
        ax.set_yticks(np.arange(0, 1.01, 0.2))
        ax.set_ylabel(metric.capitalize() + " (mean ± SE)")
        # Horizontal gridlines only
        ax.grid(axis="x", visible=False)
        ax.grid(axis="y", visible=True)
        ax.tick_params(axis="x", labelsize=7.5)

    # ── panel 3: teleport-collapse rate ──────────────────────────────────
    ax = axes[2]
    hues = [("synthetic", None)] + [("real", m) for m in model_order]
    for h_idx, (kind, model) in enumerate(hues):
        offset = (h_idx - (n_hues - 1) / 2) * bar_w_tele
        rates = []
        for v in TELEPORT_VARIANTS:
            if kind == "synthetic":
                t = teleport_synth.get(v, (np.nan, 0))
            else:
                t = teleport_real.get(model, {}).get(v, (np.nan, 0))
            rates.append(t[0])
        color_label = (
            "synthetic" if kind == "synthetic"
            else ("real_opus" if "opus" in (model or "") else "real_sonnet")
        )
        kw = _hue_kwargs(color_label)
        kw["label"] = None  # legend already on first axis
        ax.bar(
            x_tele + offset, rates, bar_w_tele,
            edgecolor="white", linewidth=0.4,
            **kw,
        )
        # NO bar value labels — axes already show the scale.

    ax.set_xticks(x_tele)
    ax.set_xticklabels([v.replace("_", "\n") for v in TELEPORT_VARIANTS])
    ax.set_ylim(0, 1.05)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.set_ylabel("Teleport-collapse rate\n(||cf_pos − dg|| < 5 cm)")
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", visible=True)

    # ── shared legend below ───────────────────────────────────────────────
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, labels,
        loc="lower center", ncols=len(labels),
        bbox_to_anchor=(0.5, -0.05), frameon=False,
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out_path))
    fig.savefig(str(out_path.with_suffix(".pdf")))
    plt.close(fig)
    print(f"wrote {out_path} (+ .pdf)")


if __name__ == "__main__":
    synth = aggregate_synthetic(SYNTH_PATH)
    real = aggregate_real(REAL_PATH)
    teleport_synth = teleport_rate_synthetic(SYNTH_PATH)
    teleport_real = teleport_rate_real(REAL_PATH)

    if not synth:
        print(f"[warn] synthetic JSON missing or empty at {SYNTH_PATH}")
    if not real:
        print(f"[warn] real JSON missing or empty at {REAL_PATH}")
        raise SystemExit(1)

    out = REPO / "agent_reports" / "figs" / "figN_c1v2_real_vs_synthetic.png"
    make_figure(synth, real, teleport_synth, teleport_real, out)
