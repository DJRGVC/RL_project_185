"""NeurIPS-style learning-curve figure v2: HER, vlm_cf, verified_cf, Oracle-CF.

Extends fig_learning_curves to include the verified_cf Phase 2 attempt-5 family
(run_name "path_c_vlm_vcf_*", created > 2026-05-12T18:20Z, finished, 500k steps,
9 runs total = 3 envs x 3 seeds).

Methods plotted per facet:
  - HER baseline    (gray; 250k horizon)
  - vlm_cf          (blue; 500k horizon)
  - verified_cf     (reddish-purple; 500k horizon; Phase 2 attempt 5)
  - Oracle-CF       (Okabe-Ito green; PnP only, 1M horizon)

Story-of-the-figure: verified_cf curves should show the cold-start regime
(flat near 0 from 0->200k as the verifier rejects most VLM proposals) then
climb steeply 200k->500k. Especially striking on FetchSlide.

Run from project root with venv active:
    .venv/bin/python agent_reports/make_fig_learning_curves_v2.py

Outputs:
    agent_reports/figs/fig_learning_curves_v2.pdf
    agent_reports/figs/fig_learning_curves_v2.png
"""
from __future__ import annotations

import pathlib
from datetime import datetime, timezone

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import wandb


# --- NeurIPS-style rcParams ----------------------------------------------- #
mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7.5,
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


# --- Palette (CB-safe) ----------------------------------------------------- #
# vlm_cf keeps CB10 blue; verified_cf uses Okabe-Ito reddish-purple so the
# two CF mechanisms read as a paired family with clear contrast.
COLORS = {
    "HER":         "#ABABAB",   # neutral gray
    "vlm_cf":      "#006BA4",   # CB10 blue
    "verified_cf": "#CC79A7",   # Okabe-Ito reddish-purple
    "Oracle-CF":   "#009E73",   # Okabe-Ito bluish-green (CB-safe)
}
PRETTY = {
    "HER":         "HER (DDPG+HER)",
    "vlm_cf":      "Semantic PER (vlm_cf, ours)",
    "verified_cf": "Semantic PER (verified_cf, ours)",
    "Oracle-CF":   "Oracle-CF (1M)",
}

ENVS = ["Push", "PnP", "Slide"]
ENV_LABEL = {
    "Push":  "FetchPush",
    "PnP":   "FetchPickAndPlace",
    "Slide": "FetchSlide",
}

ENTITY_PROJECT = "d-grant-uc-berkeley/RL_project"


def _env_from_runname(name: str) -> str | None:
    n = name.lower()
    if "_pp_" in n or n.endswith("_pp"):
        return "PnP"
    if "_push_" in n or n.endswith("_push"):
        return "Push"
    if "_sld_" in n or "_slide_" in n or n.endswith("_sld") or n.endswith("_slide"):
        return "Slide"
    return None


def discover_runs():
    api = wandb.Api()
    cutoff = datetime(2026, 5, 12, 18, 20, 0, tzinfo=timezone.utc)

    # vlm_cf attempt 5: name starts with "path_c_vlm_cf_", finished, created
    # after cutoff. Exclude the later parameter-sweep runs ("_psweep_").
    vlm_all = list(api.runs(ENTITY_PROJECT,
                            filters={"display_name": {"$regex": "^path_c_vlm_cf_"}},
                            per_page=200))
    vlm5 = []
    for r in vlm_all:
        if "_psweep_" in r.name:
            continue
        if r.state != "finished":
            continue
        ca = r.created_at
        ca_dt = datetime.fromisoformat(ca.replace("Z", "+00:00")) if isinstance(ca, str) else ca
        if ca_dt.tzinfo is None:
            ca_dt = ca_dt.replace(tzinfo=timezone.utc)
        if ca_dt > cutoff:
            vlm5.append(r)

    # verified_cf Phase 2: name starts with "path_c_vlm_vcf_", after cutoff, finished
    vcf_all = list(api.runs(ENTITY_PROJECT,
                            filters={"display_name": {"$regex": "^path_c_vlm_vcf_"}},
                            per_page=200))
    vcf = []
    for r in vcf_all:
        ca = r.created_at
        ca_dt = datetime.fromisoformat(ca.replace("Z", "+00:00")) if isinstance(ca, str) else ca
        if ca_dt.tzinfo is None:
            ca_dt = ca_dt.replace(tzinfo=timezone.utc)
        if ca_dt > cutoff and r.state == "finished":
            vcf.append(r)

    # Oracle-CF 1M PnP
    oracle = list(api.runs(ENTITY_PROJECT,
                           filters={"tags": {"$in": ["oracle_cf_1m_pnp"]}},
                           per_page=200))

    # HER baseline
    her = list(api.runs(ENTITY_PROJECT,
                        filters={"$and": [
                            {"tags": {"$in": ["path_c_overnight_2026-05-11"]}},
                            {"display_name": {"$regex": "^path_c_kill_her_"}},
                        ]},
                        per_page=200))

    return vlm5, vcf, oracle, her


def pull_history(run, key_candidates=("eval/success_rate", "charts/eval/success_rate")):
    for key in key_candidates:
        try:
            rows = list(run.scan_history(keys=["global_step", key]))
        except Exception:
            rows = []
        if not rows:
            continue
        steps = np.array([r.get("global_step") for r in rows if r.get("global_step") is not None],
                         dtype=float)
        vals = np.array([r.get(key) for r in rows if r.get(key) is not None],
                        dtype=float)
        if steps.size and vals.size and steps.size == vals.size:
            order = np.argsort(steps)
            return steps[order], vals[order]
    return np.array([]), np.array([])


def aggregate(seed_curves, common_grid):
    interps = []
    for steps, vals in seed_curves:
        if steps.size == 0:
            continue
        lo, hi = steps.min(), steps.max()
        v = np.interp(common_grid, steps, vals, left=np.nan, right=np.nan)
        v = np.where((common_grid >= lo) & (common_grid <= hi), v, np.nan)
        interps.append(v)
    if not interps:
        return None, None, None
    arr = np.vstack(interps)
    with np.errstate(all="ignore"):
        mean = np.nanmean(arr, axis=0)
        std = np.nanstd(arr, axis=0, ddof=1) if arr.shape[0] > 1 else np.zeros_like(mean)
        n = np.sum(~np.isnan(arr), axis=0)
        se = std / np.sqrt(np.maximum(n, 1))
    return mean, se, n


def make_figure(out_dir: pathlib.Path):
    print("Discovering W&B runs ...")
    vlm5, vcf, oracle, her = discover_runs()
    print(f"  vlm_cf attempt 5:    {len(vlm5)} runs")
    print(f"  verified_cf attempt 5: {len(vcf)} runs")
    print(f"  oracle_cf_1m_pnp:    {len(oracle)} runs")
    print(f"  HER baseline:        {len(her)} runs")
    assert len(vlm5) == 9, f"expected 9 vlm_cf, got {len(vlm5)}"
    assert len(vcf) == 9, f"expected 9 verified_cf, got {len(vcf)}"
    assert len(oracle) == 3, f"expected 3 oracle_cf, got {len(oracle)}"
    assert len(her) == 9, f"expected 9 her, got {len(her)}"

    data = {m: {e: [] for e in ENVS}
            for m in ("HER", "vlm_cf", "verified_cf", "Oracle-CF")}

    print("Pulling histories ...")
    for r in vlm5:
        env = _env_from_runname(r.name)
        if env is None:
            print(f"  WARN: cant parse env from {r.name}"); continue
        s, v = pull_history(r)
        print(f"  vlm_cf      {r.name}: env={env} n_pts={len(s)} max_step={s.max() if s.size else 0:.0f}")
        if s.size:
            data["vlm_cf"][env].append((s, v))

    for r in vcf:
        env = _env_from_runname(r.name)
        if env is None:
            print(f"  WARN: cant parse env from {r.name}"); continue
        s, v = pull_history(r)
        print(f"  verified_cf {r.name}: env={env} n_pts={len(s)} max_step={s.max() if s.size else 0:.0f}")
        if s.size:
            data["verified_cf"][env].append((s, v))

    for r in oracle:
        s, v = pull_history(r)
        print(f"  oracle      {r.name}: n_pts={len(s)} max_step={s.max() if s.size else 0:.0f}")
        if s.size:
            data["Oracle-CF"]["PnP"].append((s, v))

    for r in her:
        env = _env_from_runname(r.name)
        if env is None:
            print(f"  WARN: cant parse env from {r.name}"); continue
        s, v = pull_history(r)
        print(f"  her         {r.name}: env={env} n_pts={len(s)} max_step={s.max() if s.size else 0:.0f}")
        if s.size:
            data["HER"][env].append((s, v))

    # --- Build figure ----------------------------------------------------- #
    fig, axes = plt.subplots(1, 3, figsize=(6.75, 2.6), sharey=True)
    fig.subplots_adjust(left=0.085, right=0.985, bottom=0.26, top=0.93, wspace=0.10)

    plot_order = ["HER", "vlm_cf", "verified_cf", "Oracle-CF"]

    for ax, env in zip(axes, ENVS):
        seed_maxes = []
        for m in data:
            for s, _ in data[m][env]:
                if s.size:
                    seed_maxes.append(s.max())
        if not seed_maxes:
            continue
        max_step = max(seed_maxes)
        grid = np.linspace(0, max_step, 400)

        for method in plot_order:
            seeds = data[method][env]
            if not seeds:
                continue
            mean, se, n = aggregate(seeds, grid)
            if mean is None:
                continue
            color = COLORS[method]
            label = PRETTY[method] if env == ENVS[0] or (env == "PnP" and method == "Oracle-CF") else None
            ax.fill_between(grid, mean - se, mean + se, color=color, alpha=0.20, linewidth=0)
            ax.plot(grid, mean, color=color, linewidth=1.4, label=label, zorder=3)

            for s, v in seeds:
                if s.size == 0:
                    continue
                ax.scatter([s[-1]], [v[-1]], s=12, color="white",
                           edgecolors=color, linewidths=0.9, zorder=5, clip_on=False)

        ax.set_xlim(0, max_step * 1.01)
        ax.set_ylim(0.0, 1.0)
        ax.set_yticks(np.arange(0, 1.01, 0.2))
        ax.grid(axis="x", visible=False)
        ax.set_xlabel("Training steps")
        if max_step >= 900_000:
            xticks = [0, 250_000, 500_000, 750_000, 1_000_000]
        elif max_step >= 450_000:
            xticks = [0, 100_000, 200_000, 300_000, 400_000, 500_000]
        else:
            xticks = [0, 50_000, 100_000, 150_000, 200_000, 250_000]
        ax.set_xticks(xticks)
        ax.set_xticklabels([_fmt_step(t) for t in xticks])
        ax.text(0.03, 0.95, ENV_LABEL[env], transform=ax.transAxes,
                ha="left", va="top", fontsize=8.5, fontweight="bold", color="#333333")

    axes[0].set_ylabel("Eval success rate")

    # Build legend across all axes, sorted by plot_order priority.
    handles, labels = [], []
    for ax in axes:
        h, l = ax.get_legend_handles_labels()
        for hh, ll in zip(h, l):
            if ll not in labels:
                handles.append(hh)
                labels.append(ll)
    order_pref = [PRETTY[m] for m in plot_order]
    sorted_pairs = sorted(zip(handles, labels),
                          key=lambda p: order_pref.index(p[1]) if p[1] in order_pref else 99)
    handles, labels = zip(*sorted_pairs) if sorted_pairs else ([], [])

    # Legend below the panels: 4 columns of 1 entry each.
    leg = fig.legend(handles, labels,
                     loc="lower center",
                     bbox_to_anchor=(0.5, -0.02),
                     ncols=4,
                     handlelength=1.8,
                     handletextpad=0.5,
                     columnspacing=1.6,
                     borderpad=0.3,
                     labelspacing=0.25,
                     frameon=False)

    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / "fig_learning_curves_v2.pdf"
    png_path = out_dir / "fig_learning_curves_v2.png"
    fig.savefig(pdf_path, bbox_extra_artists=(leg,))
    fig.savefig(png_path, bbox_extra_artists=(leg,))
    plt.close(fig)
    print(f"Wrote {pdf_path}")
    print(f"Wrote {png_path}")


def _fmt_step(s: float) -> str:
    if s <= 0:
        return "0"
    if s >= 1_000_000:
        v = s / 1_000_000
        return f"{v:.1f}M".replace(".0M", "M")
    if s >= 1_000:
        v = s / 1_000
        return f"{v:.0f}k"
    return f"{s:.0f}"


if __name__ == "__main__":
    figs_dir = pathlib.Path(__file__).parent / "figs"
    make_figure(figs_dir)
    print("Done.")
