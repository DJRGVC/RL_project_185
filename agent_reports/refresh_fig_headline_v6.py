"""Auto-refresh the headline bar chart to v6 once HER@1M Push+Slide finishes.

Story:
  - v5 has HER@1M PnP folded in; Push and Slide still show 250k baseline.
  - As soon as all 9 HER@1M runs (3 envs × 3 seeds) are finished on W&B,
    v6 should be regenerated with the *real* 1M numbers for ALL three envs.

This script:
  1. Polls W&B for runs tagged ``path_c_her_1m`` (Push/Slide) and
     ``her_baseline_1m`` (PnP, already done).
  2. If <9 finished, prints a status line and exits 0 (graceful skip).
  3. If 9 finished, pulls each seed's final eval/success_rate, regenerates
     ``agent_reports/figs/fig_headline_v6.{png,pdf}``, and writes a
     companion ``agent_reports/_her_1m_seed_table.md`` for paper provenance.
  4. IDEMPOTENT: if v6 already exists AND its embedded HER values match
     the W&B numbers, the script exits 0 without rewriting.

Does NOT modify any paper LaTeX. Updating ``\\includegraphics{...v5}`` →
``...v6`` is the paper agent's job.

Run from project root with venv active:
    .venv/bin/python agent_reports/refresh_fig_headline_v6.py

Optional:
    --dry-run    Skip W&B query; print expected behavior and exit 0.
    --force      Always regenerate even if up-to-date.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from datetime import datetime

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

# --- Config ----------------------------------------------------------------
ENTITY_PROJECT = "d-grant-uc-berkeley/RL_project"

# HER@1M tags by env:
HER_1M_TAGS = ["path_c_her_1m", "her_baseline_1m", "path_c_her_1m_pnp"]

ENVS = ["FetchPush", "FetchPickAndPlace", "FetchSlide"]
ENV_SLUG_TO_LABEL = {"push": "FetchPush", "pp": "FetchPickAndPlace", "slide": "FetchSlide"}
SEEDS = [42, 123, 999]

EVAL_KEYS = ("eval/success_rate", "charts/eval/success_rate")
FINAL_WINDOW = 5

PROVENANCE_PATH_NAME = "_her_1m_seed_table.md"
V6_STATE_FILE_NAME = "_fig_headline_v6_state.json"

# Run-name parser, e.g. "path_c_her_1m_pp_s42_seed42",
#                       "path_c_her_1m_push_s123_seed123",
#                       "path_c_her_1m_slide_s999_seed999"
HER_RE = re.compile(
    r"path_c_her_1m_(?P<env>pp|push|slide)_s(?P<seed>\d+)"
)


# --- NeurIPS rcParams (matches v5) -----------------------------------------
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


# --- W&B helpers -----------------------------------------------------------
def pull_final_sr(run, window: int = FINAL_WINDOW):
    for key in EVAL_KEYS:
        try:
            rows = list(run.scan_history(keys=["global_step", key]))
        except Exception:
            rows = []
        if not rows:
            continue
        steps = [r.get("global_step") for r in rows if r.get("global_step") is not None]
        vals = [r.get(key) for r in rows if r.get(key) is not None]
        if not steps or not vals or len(steps) != len(vals):
            continue
        order = np.argsort(np.asarray(steps, dtype=float))
        vals_a = np.asarray(vals, dtype=float)[order]
        tail = vals_a[-min(window, len(vals_a)):]
        return float(np.nanmean(tail))
    try:
        s = run.summary
        for key in EVAL_KEYS:
            if key in s and s[key] is not None:
                return float(s[key])
    except Exception:
        pass
    return None


def fetch_her_1m_runs():
    import wandb
    api = wandb.Api()

    # Pull anything with a HER@1M tag, then filter by run name.
    runs = []
    seen_ids = set()
    for tag in HER_1M_TAGS:
        for r in api.runs(ENTITY_PROJECT,
                          filters={"tags": {"$in": [tag]}},
                          per_page=200):
            if r.id in seen_ids:
                continue
            seen_ids.add(r.id)
            runs.append(r)

    # Bucket: data[env_slug][seed] = (final_sr, state)
    data = {"push": {}, "pp": {}, "slide": {}}
    for r in runs:
        m = HER_RE.match(r.name)
        if not m:
            continue
        env_slug = m.group("env")
        seed = int(m.group("seed"))
        if seed not in SEEDS:
            continue
        final = pull_final_sr(r) if r.state in ("finished", "running") else None
        # Prefer "finished" over "running" if both somehow exist.
        prev = data[env_slug].get(seed)
        if prev is None or (prev["state"] != "finished" and r.state == "finished"):
            data[env_slug][seed] = {
                "final_sr": final,
                "state": r.state,
                "run_name": r.name,
            }
    return data


def all_complete(data) -> bool:
    for env_slug in ("push", "pp", "slide"):
        d = data.get(env_slug, {})
        for seed in SEEDS:
            cell = d.get(seed)
            if cell is None or cell["state"] != "finished" or cell["final_sr"] is None:
                return False
    return True


# --- Static (non-HER) data — pulled forward from v5 ------------------------
# Keeping these inline matches v5's style: keep the figure self-contained and
# auditable rather than re-querying every static baseline.

SEEDS_STATIC = {
    ("Oracle-CF", "FetchPush"): [0.300, 0.250, 0.600],
    ("Oracle-CF", "FetchPickAndPlace"): [0.30, 0.90, 0.55],
    ("Oracle-CF", "FetchSlide"): [0.200, 0.200, 0.150],
    ("vlm_cf", "FetchPush"): [1.00, 0.95, 0.90],
    ("vlm_cf", "FetchPickAndPlace"): [0.35, 0.35, 0.50],
    ("vlm_cf", "FetchSlide"): [0.25, 0.70, 0.70],
    ("verified_cf", "FetchPush"):        [0.65, 0.90, 1.00],
    ("verified_cf", "FetchPickAndPlace"): [0.25, 0.30, 0.50],
    ("verified_cf", "FetchSlide"):       [0.60, 0.65, 0.60],
}

SUMMARY_MEAN_SE_STATIC = {
    ("Uniform", "FetchPush"): (0.08, 0.05),
    ("Uniform", "FetchPickAndPlace"): (0.07, 0.05),
    ("Uniform", "FetchSlide"): (0.08, 0.07),
    ("PER", "FetchPush"): (0.95, 0.02),
    ("PER", "FetchPickAndPlace"): (0.10, 0.04),
    ("PER", "FetchSlide"): (0.10, 0.06),
}

HORIZON_STATIC = {
    ("Uniform", "FetchPush"): "3M",
    ("Uniform", "FetchPickAndPlace"): "3M",
    ("Uniform", "FetchSlide"): "3M",
    ("PER", "FetchPush"): "3M",
    ("PER", "FetchPickAndPlace"): "3M",
    ("PER", "FetchSlide"): "3M",
    ("Oracle-CF", "FetchPush"): "250k",
    ("Oracle-CF", "FetchPickAndPlace"): "1M",
    ("Oracle-CF", "FetchSlide"): "250k",
    ("vlm_cf", "FetchPush"): "500k",
    ("vlm_cf", "FetchPickAndPlace"): "500k",
    ("vlm_cf", "FetchSlide"): "500k",
    ("verified_cf", "FetchPush"): "500k",
    ("verified_cf", "FetchPickAndPlace"): "500k",
    ("verified_cf", "FetchSlide"): "500k",
}

METHODS = ["Uniform", "PER", "HER", "Oracle-CF", "vlm_cf", "verified_cf"]
PALETTE = {
    "Uniform":     "#ABABAB",
    "PER":         "#5F9ED1",
    "HER":         "#FF800E",
    "Oracle-CF":   "#009E73",
    "vlm_cf":      "#006BA4",
    "verified_cf": "#CC79A7",
}
DISPLAY = {
    "Uniform":     "Uniform",
    "PER":         "PER",
    "HER":         "HER",
    "Oracle-CF":   "Oracle-CF",
    "vlm_cf":      "vlm_cf (ours)",
    "verified_cf": "verified_cf (ours)",
}


# --- Aggregation -----------------------------------------------------------
def build_her_1m_seeds(data):
    """Return {(method, env): [seeds...]} for HER@1M plus per-cell horizon."""
    out_seeds = {}
    for env_slug, env_label in ENV_SLUG_TO_LABEL.items():
        cells = data[env_slug]
        seeds_vals = [cells[s]["final_sr"] for s in SEEDS]
        out_seeds[("HER", env_label)] = seeds_vals
    return out_seeds


def _agg(method, env, her_seeds):
    if method == "HER":
        seeds = her_seeds.get((method, env))
        if seeds is None or any(v is None for v in seeds):
            return None, None, None
        arr = np.asarray(seeds, dtype=float)
        return float(arr.mean()), float(arr.std(ddof=1) / np.sqrt(arr.size)), arr
    seeds = SEEDS_STATIC.get((method, env))
    if seeds is not None:
        arr = np.asarray(seeds, dtype=float)
        return float(arr.mean()), float(arr.std(ddof=1) / np.sqrt(arr.size)), arr
    if (method, env) in SUMMARY_MEAN_SE_STATIC:
        m, s = SUMMARY_MEAN_SE_STATIC[(method, env)]
        return float(m), float(s), None
    return None, None, None


# --- Plot ------------------------------------------------------------------
def make_v6(out_dir: pathlib.Path, her_seeds, her_horizon_label: str = "1M"):
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    x = np.arange(len(ENVS))
    n = len(METHODS)
    bar_w = 0.86 / n

    drawn = set()
    for i, m in enumerate(METHODS):
        offset = (i - (n - 1) / 2) * bar_w
        for j, env in enumerate(ENVS):
            mean, se, seeds = _agg(m, env, her_seeds)
            if mean is None:
                continue
            xpos = x[j] + offset
            ax.bar(
                xpos, mean, bar_w,
                yerr=se, color=PALETTE[m],
                edgecolor="white", linewidth=0.4,
                error_kw=dict(elinewidth=0.7, capsize=2.0,
                              capthick=0.7, ecolor="#333333"),
                label=f"{DISPLAY[m]}" if m not in drawn else None,
                zorder=3,
            )
            drawn.add(m)

            if seeds is not None and seeds.size > 0:
                rng = np.random.default_rng(42 + i * 17 + j * 3)
                jitter = rng.uniform(-bar_w * 0.22, bar_w * 0.22, size=seeds.size)
                ax.scatter(
                    np.full_like(seeds, xpos) + jitter,
                    seeds,
                    s=12, color="white",
                    edgecolors="#222222", linewidths=0.6,
                    zorder=5, clip_on=True,
                )

            if m == "HER":
                h_label = her_horizon_label
            else:
                h_label = HORIZON_STATIC.get((m, env))
            if h_label is not None:
                ax.annotate(
                    h_label,
                    xy=(xpos, 0),
                    xytext=(0, -2),
                    textcoords="offset points",
                    ha="center", va="top",
                    fontsize=6.0, color="#777777", style="italic",
                    annotation_clip=False,
                )

    # HER per-env reference dashed line — now all at 1M.
    her_line_added = False
    for j, env in enumerate(ENVS):
        mean, _, _ = _agg("HER", env, her_seeds)
        if mean is None:
            continue
        x_left = x[j] - 0.45
        x_right = x[j] + 0.45
        ref_label = "HER reference (1M, all envs)" if not her_line_added else None
        ax.hlines(
            mean, x_left, x_right,
            colors="#555555", linestyles=(0, (4, 2)),
            linewidth=0.9, alpha=0.7, zorder=2,
            label=ref_label,
        )
        her_line_added = True

    ax.set_xticks(x)
    ax.tick_params(axis="x", pad=10)
    ax.set_xticklabels(ENVS)
    ax.set_ylabel("Final success rate (mean ±SE, n=3)")
    ax.set_ylim(0, 1.08)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.grid(axis="x", visible=False)

    handles, labels = ax.get_legend_handles_labels()
    seed_proxy = ax.scatter([], [], s=12, color="white",
                            edgecolors="#222222", linewidths=0.6,
                            label="individual seeds")
    handles.append(seed_proxy)
    labels.append("individual seeds")
    leg = ax.legend(
        handles, labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.20),
        ncols=4, columnspacing=1.2,
        handlelength=1.4, handletextpad=0.5,
        borderpad=0.4, labelspacing=0.4,
    )

    ax.annotate(
        "Italic gray stamp under each bar = training horizon for that cell.  "
        "v6 update: HER bars across all three envs now use the 1M-step "
        "horizon (n=3 seeds each).  Cross-horizon comparisons read as "
        "sample-efficiency claims, not asymptotic dominance.",
        xy=(0.5, -0.40), xycoords="axes fraction",
        ha="center", va="top",
        fontsize=6.8, color="#666666", style="italic",
        wrap=True,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / "fig_headline_v6.png"
    pdf = out_dir / "fig_headline_v6.pdf"
    fig.savefig(png, bbox_extra_artists=(leg,))
    fig.savefig(pdf, bbox_extra_artists=(leg,))
    plt.close(fig)
    print(f"[v6] wrote {png}")
    print(f"[v6] wrote {pdf}")


def write_provenance_md(data, out_path: pathlib.Path):
    lines = [
        "# HER@1M final success rates — provenance for fig_headline_v6",
        "",
        f"Generated: {datetime.utcnow().isoformat(timespec='seconds')}Z",
        "Tags polled: " + ", ".join(f"`{t}`" for t in HER_1M_TAGS),
        "",
        "Final SR = mean of last 5 eval points (eval/success_rate).",
        "",
        "| Env              | Seed | Final SR | State    | Run name |",
        "|------------------|------|----------|----------|----------|",
    ]
    for env_slug in ("push", "pp", "slide"):
        label = ENV_SLUG_TO_LABEL[env_slug]
        for seed in SEEDS:
            cell = data.get(env_slug, {}).get(seed)
            if cell is None:
                lines.append(f"| {label:<16} | {seed:<4} | (missing) | —        | — |")
            else:
                sr = "—" if cell["final_sr"] is None else f"{cell['final_sr']:.3f}"
                lines.append(
                    f"| {label:<16} | {seed:<4} | {sr:<8} | {cell['state']:<8} "
                    f"| `{cell['run_name']}` |"
                )
    out_path.write_text("\n".join(lines) + "\n")
    print(f"[v6] wrote {out_path}")


def compute_state_hash(her_seeds) -> dict:
    """Round to 4 decimals so identical W&B numbers hash identically."""
    out = {}
    for env in ENVS:
        seeds = her_seeds.get(("HER", env), [])
        out[env] = [round(float(s), 4) if s is not None else None for s in seeds]
    return out


def state_matches(state_file: pathlib.Path, current: dict) -> bool:
    if not state_file.exists():
        return False
    try:
        prev = json.loads(state_file.read_text())
    except Exception:
        return False
    return prev.get("her_seeds") == current


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    here = pathlib.Path(__file__).parent
    figs_dir = here / "figs"
    state_file = here / V6_STATE_FILE_NAME

    if args.dry_run:
        print("[v6] --dry-run: skipping W&B query.")
        print("[v6] would poll tags:", HER_1M_TAGS)
        print("[v6] would write fig_headline_v6.{png,pdf} when 9/9 finished.")
        return 0

    try:
        data = fetch_her_1m_runs()
    except Exception as e:
        print(f"[v6] W&B query failed: {e!r}", file=sys.stderr)
        print("[v6] exiting 0 (graceful — caller can retry later).")
        return 0

    # Status summary
    counts = {"push": 0, "pp": 0, "slide": 0}
    for env_slug in counts:
        for seed in SEEDS:
            cell = data.get(env_slug, {}).get(seed)
            if cell is not None and cell["state"] == "finished":
                counts[env_slug] += 1
    print(f"[v6] finished — Push: {counts['push']}/3, "
          f"PnP: {counts['pp']}/3, Slide: {counts['slide']}/3")

    if not all_complete(data):
        total = sum(counts.values())
        print(f"[v6] NOT READY: only {total}/9 HER@1M runs finished. "
              "Exiting 0 (will retry on next invocation).")
        return 0

    her_seeds = build_her_1m_seeds(data)
    new_state = compute_state_hash(her_seeds)

    png = figs_dir / "fig_headline_v6.png"
    pdf = figs_dir / "fig_headline_v6.pdf"

    if (not args.force
            and png.exists() and pdf.exists()
            and state_matches(state_file, new_state)):
        print("[v6] fig_headline_v6 already up-to-date (state hash matches). "
              "Skipping.  Pass --force to override.")
        return 0

    make_v6(figs_dir, her_seeds)
    write_provenance_md(data, here / PROVENANCE_PATH_NAME)
    state_file.write_text(json.dumps(
        {"her_seeds": new_state,
         "generated": datetime.utcnow().isoformat(timespec='seconds') + "Z"},
        indent=2))
    print(f"[v6] wrote state file {state_file}")
    print("[v6] DONE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
