"""Aggregator + figure + paragraph for the VLM-CF p_counterfactual sweep.

Pulls every run tagged ``path_c_vlm_cf_psweep_2026-05-12`` from W&B,
groups by p ∈ {0.00, 0.10, 0.25, 0.50, 0.75, 1.00} and seed ∈ {42, 123, 999},
and emits three artifacts ready to drop into the paper:

  - ``agent_reports/_psweep_results.md``        — Markdown table
  - ``agent_reports/figs/fig_psweep.{png,pdf}`` — NeurIPS-style bar chart
  - ``agent_reports/_psweep_paragraph.tex``     — paste-ready LaTeX prose

The sweep is FetchPickAndPlace-v4 only (n=3 seeds per p), so this is a
six-bar single-panel chart.  Style follows the NeurIPS conventions pinned
in ``~/.claude/.../feedback_neurips_figures.md``: no chart title, CB-safe
palette, sans-serif, vector PDF, mean ± SE with seed dots overlaid.

The script is IDEMPOTENT and GRACEFUL:
  - If <18 runs are finished it still produces best-effort outputs and
    marks incomplete p-values with "pending (n/3)" rather than crashing.
  - Re-running overwrites the outputs but never deletes other files.
  - If zero finished runs match, the script prints a clear message and
    exits 0.

Run from project root with venv active:
    .venv/bin/python agent_reports/make_psweep_analysis.py

Optional flags:
    --dry-run    Skip the W&B query; print what would happen and exit 0.
    --tag TAG    Override the tag filter (default path_c_vlm_cf_psweep_2026-05-12).
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys
from datetime import datetime

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

# --- Config ----------------------------------------------------------------
ENTITY_PROJECT = "d-grant-uc-berkeley/RL_project"
DEFAULT_TAG = "path_c_vlm_cf_psweep_2026-05-12"

# p ∈ {0.00, 0.10, 0.25, 0.50, 0.75, 1.00}, encoded as "00/10/25/50/75/100"
P_TOKENS = ["00", "10", "25", "50", "75", "100"]
P_FLOAT = {"00": 0.00, "10": 0.10, "25": 0.25, "50": 0.50, "75": 0.75, "100": 1.00}
SEEDS = [42, 123, 999]

# Eval key candidates — same priority as make_fig_learning_curves_v2.py
EVAL_KEYS = ("eval/success_rate", "charts/eval/success_rate")

# Final-success window: average of last K eval points to smooth noise.
FINAL_WINDOW = 5


# --- NeurIPS rcParams ------------------------------------------------------
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


# --- W&B parsing helpers ---------------------------------------------------
RUN_RE = re.compile(
    r"path_c_vlm_cf_psweep_p(?P<p>\d{2,3})_(?P<env>pp|push|slide)_s(?P<seed>\d+)"
)


def parse_run_name(name: str):
    m = RUN_RE.match(name)
    if not m:
        return None
    p_tok = m.group("p")
    if p_tok not in P_TOKENS:
        return None
    seed = int(m.group("seed"))
    if seed not in SEEDS:
        return None
    return p_tok, m.group("env"), seed


def pull_final_sr(run, window: int = FINAL_WINDOW):
    """Return (final_sr, max_step) using last `window` eval points, or (None, None)."""
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
        steps_a = np.asarray(steps, dtype=float)
        vals_a = np.asarray(vals, dtype=float)
        order = np.argsort(steps_a)
        steps_a = steps_a[order]
        vals_a = vals_a[order]
        # Average the last `window` eval points.
        tail = vals_a[-min(window, len(vals_a)):]
        return float(np.nanmean(tail)), float(steps_a[-1])
    # Fall back to run summary if available
    try:
        s = run.summary
        for key in EVAL_KEYS:
            if key in s and s[key] is not None:
                return float(s[key]), None
    except Exception:
        pass
    return None, None


def fetch_psweep_runs(tag: str):
    """Return {p_token: {seed: (final_sr, state, max_step, run_name)}}."""
    import wandb  # late import so --dry-run works without wandb auth

    api = wandb.Api()
    runs = list(api.runs(
        ENTITY_PROJECT,
        filters={"tags": {"$in": [tag]}},
        per_page=200,
    ))
    print(f"[psweep] tag={tag!r}: {len(runs)} runs matched", flush=True)

    table = {p: {} for p in P_TOKENS}
    n_finished = 0
    n_running = 0
    n_other = 0

    for r in runs:
        parsed = parse_run_name(r.name)
        if parsed is None:
            print(f"  skip unparseable: {r.name}")
            continue
        p_tok, env, seed = parsed
        if env != "pp":
            # The sweep was defined as PnP-only, but be defensive.
            print(f"  skip non-pp env: {r.name}")
            continue
        state = r.state
        if state == "finished":
            n_finished += 1
            final, max_step = pull_final_sr(r)
        elif state == "running":
            n_running += 1
            final, max_step = pull_final_sr(r)  # partial credit allowed but flagged
        else:
            n_other += 1
            final, max_step = pull_final_sr(r)
        table[p_tok][seed] = {
            "final_sr": final,
            "state": state,
            "max_step": max_step,
            "run_name": r.name,
        }

    print(f"[psweep] finished={n_finished}  running={n_running}  other={n_other}")
    return table


# --- Aggregation -----------------------------------------------------------
def summarize(table):
    """Return list of dicts per p, sorted by p value."""
    rows = []
    for p_tok in P_TOKENS:
        seeds_data = table.get(p_tok, {})
        finished_vals = []
        all_vals = []
        per_seed = {}
        for seed in SEEDS:
            d = seeds_data.get(seed)
            if d is None:
                per_seed[seed] = None
                continue
            per_seed[seed] = d
            if d["final_sr"] is not None:
                all_vals.append(d["final_sr"])
                if d["state"] == "finished":
                    finished_vals.append(d["final_sr"])
        if finished_vals:
            arr = np.asarray(finished_vals, dtype=float)
            mean = float(arr.mean())
            se = float(arr.std(ddof=1) / np.sqrt(arr.size)) if arr.size > 1 else 0.0
        else:
            mean, se = None, None
        rows.append({
            "p_token": p_tok,
            "p_float": P_FLOAT[p_tok],
            "n_finished": len(finished_vals),
            "n_total": len([v for v in per_seed.values() if v is not None]),
            "mean_sr": mean,
            "se_sr": se,
            "finished_vals": finished_vals,
            "all_vals": all_vals,
            "per_seed": per_seed,
        })
    return rows


# --- Outputs ---------------------------------------------------------------
def write_table_md(rows, out_path: pathlib.Path, tag: str) -> None:
    lines = []
    lines.append("# VLM-CF p_counterfactual sweep — final success rates\n")
    lines.append(f"Tag: `{tag}`")
    lines.append(f"Generated: {datetime.utcnow().isoformat(timespec='seconds')}Z")
    lines.append(f"Env: FetchPickAndPlace-v4   Horizon: 500k   Seeds: {SEEDS}\n")
    lines.append("Final success rate = mean of last "
                 f"{FINAL_WINDOW} eval points; SE computed across n_finished seeds (ddof=1).\n")
    lines.append("| p     | n_finished/3 | mean SR | SE     | s42      | s123     | s999     |")
    lines.append("|-------|--------------|---------|--------|----------|----------|----------|")
    for row in rows:
        p = row["p_float"]
        n = row["n_finished"]
        mean = "—" if row["mean_sr"] is None else f"{row['mean_sr']:.3f}"
        se = "—" if row["se_sr"] is None else f"{row['se_sr']:.3f}"
        cells = []
        for seed in SEEDS:
            d = row["per_seed"].get(seed)
            if d is None:
                cells.append("—")
            elif d["final_sr"] is None:
                cells.append(f"({d['state']})")
            else:
                tag_state = "" if d["state"] == "finished" else f"({d['state']})"
                cells.append(f"{d['final_sr']:.3f}{tag_state}")
        lines.append(f"| {p:.2f} | {n}/3          | {mean:>7} | {se:>6} | "
                     f"{cells[0]:<8} | {cells[1]:<8} | {cells[2]:<8} |")
    lines.append("")
    # Best-p line
    finished_rows = [r for r in rows if r["mean_sr"] is not None and r["n_finished"] == 3]
    if finished_rows:
        best = max(finished_rows, key=lambda r: r["mean_sr"])
        lines.append(f"**Best p (fully complete only):** p={best['p_float']:.2f} "
                     f"with mean SR = {best['mean_sr']:.3f} ± {best['se_sr']:.3f}")
    else:
        partial = [r for r in rows if r["mean_sr"] is not None]
        if partial:
            best = max(partial, key=lambda r: r["mean_sr"])
            lines.append(f"**Best p (partial; some cells <3 seeds):** p={best['p_float']:.2f} "
                         f"with mean SR = {best['mean_sr']:.3f} ± {best['se_sr']:.3f}")
        else:
            lines.append("**No finished runs yet — table is empty.**")
    out_path.write_text("\n".join(lines))
    print(f"[psweep] wrote {out_path}")


def make_bar_chart(rows, out_dir: pathlib.Path, tag: str) -> None:
    fig, ax = plt.subplots(figsize=(4.0, 2.8))

    xs = np.arange(len(rows))
    means = [r["mean_sr"] if r["mean_sr"] is not None else 0.0 for r in rows]
    ses = [r["se_sr"] if r["se_sr"] is not None else 0.0 for r in rows]
    has_data = [r["mean_sr"] is not None for r in rows]

    # CB-safe palette: viridis-ish gradient over p indexes the p value visually.
    cmap = plt.get_cmap("viridis")
    colors = [cmap(0.15 + 0.7 * (i / max(len(rows) - 1, 1))) for i in range(len(rows))]

    for i, row in enumerate(rows):
        if not has_data[i]:
            # Hollow placeholder bar
            ax.bar(xs[i], 0.0, 0.7, color="white", edgecolor="#999999",
                   linewidth=0.6, hatch="//", zorder=2,
                   label=None)
            continue
        ax.bar(
            xs[i], means[i], 0.7,
            yerr=ses[i] if ses[i] > 0 else None,
            color=colors[i],
            edgecolor="white", linewidth=0.4,
            error_kw=dict(elinewidth=0.7, capsize=2.0,
                          capthick=0.7, ecolor="#333333"),
            zorder=3,
        )

        # Seed dots (over the bar)
        vals = row["finished_vals"] + [v for v in row["all_vals"] if v not in row["finished_vals"]]
        if vals:
            rng = np.random.default_rng(42 + i)
            jitter = rng.uniform(-0.18, 0.18, size=len(vals))
            # Closed dots for finished seeds, open dots for partial (running)
            n_fin = len(row["finished_vals"])
            for k, v in enumerate(vals):
                is_fin = k < n_fin
                ax.scatter(
                    xs[i] + jitter[k], v,
                    s=14,
                    color="white" if is_fin else "none",
                    edgecolors="#222222",
                    linewidths=0.7 if is_fin else 0.6,
                    zorder=5, clip_on=True,
                )

        # Annotate "n/3" if not complete
        if row["n_finished"] < 3:
            ax.annotate(f"n={row['n_finished']}/3",
                        xy=(xs[i], means[i] + (ses[i] if ses[i] else 0) + 0.02),
                        ha="center", va="bottom",
                        fontsize=6.5, color="#666666", style="italic",
                        annotation_clip=False)

    ax.set_xticks(xs)
    ax.set_xticklabels([f"{r['p_float']:.2f}" for r in rows])
    ax.set_xlabel(r"$p_{\mathrm{counterfactual}}$")
    ax.set_ylabel("Final success rate (mean ±SE, n=3)")
    ax.set_ylim(0, 1.05)
    ax.set_yticks(np.arange(0, 1.01, 0.2))
    ax.grid(axis="x", visible=False)

    # Seed-dot legend proxy
    fin_proxy = ax.scatter([], [], s=14, color="white",
                           edgecolors="#222222", linewidths=0.7,
                           label="finished seed")
    run_proxy = ax.scatter([], [], s=14, facecolors="none",
                           edgecolors="#222222", linewidths=0.6,
                           label="running seed (partial)")
    handles = [fin_proxy, run_proxy]
    labels = ["finished seed", "running seed (partial)"]

    ax.legend(handles, labels,
              loc="upper center",
              bbox_to_anchor=(0.5, -0.22),
              ncols=2,
              columnspacing=1.2,
              handlelength=1.2,
              handletextpad=0.4,
              borderpad=0.3)

    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / "fig_psweep.png"
    pdf = out_dir / "fig_psweep.pdf"
    fig.savefig(png)
    fig.savefig(pdf)
    plt.close(fig)
    print(f"[psweep] wrote {png}")
    print(f"[psweep] wrote {pdf}")


def write_paragraph_tex(rows, out_path: pathlib.Path, tag: str) -> None:
    finished_rows = [r for r in rows if r["mean_sr"] is not None and r["n_finished"] == 3]
    partial_rows = [r for r in rows if r["mean_sr"] is not None and r["n_finished"] < 3]
    pending_rows = [r for r in rows if r["mean_sr"] is None]

    if not finished_rows and not partial_rows:
        body = (
            "% Auto-generated p-sweep paragraph (no finished runs yet).\n"
            "% Re-run agent_reports/make_psweep_analysis.py once runs complete.\n"
            "% No data available to write paragraph.\n"
        )
        out_path.write_text(body)
        print(f"[psweep] wrote {out_path} (placeholder — no data)")
        return

    # Build summary text.
    all_summary = sorted(finished_rows, key=lambda r: r["p_float"])
    if all_summary:
        best = max(all_summary, key=lambda r: r["mean_sr"])
        worst = min(all_summary, key=lambda r: r["mean_sr"])
        scope = (f"All {len(all_summary)} fully-complete cells (3/3 seeds)"
                 if len(all_summary) == len(P_TOKENS)
                 else f"{len(all_summary)} of {len(P_TOKENS)} cells fully complete")
    else:
        best = max(partial_rows, key=lambda r: r["mean_sr"])
        worst = min(partial_rows, key=lambda r: r["mean_sr"])
        scope = "preliminary (some cells <3 seeds)"

    # Render row-by-row mean ± SE table inline.
    fragments = []
    for r in sorted(finished_rows + partial_rows, key=lambda r: r["p_float"]):
        marker = "" if r["n_finished"] == 3 else f"$^\\dagger$"
        fragments.append(f"$p\\!=\\!{r['p_float']:.2f}$: ${r['mean_sr']:.2f}\\pm{r['se_sr']:.2f}${marker}")
    inline_results = ", ".join(fragments)

    pending_note = ""
    if pending_rows or partial_rows:
        pending_p_vals = [f"{r['p_float']:.2f}" for r in pending_rows + partial_rows]
        pending_note = (f"  Cells at $p\\!\\in\\!\\{{{', '.join(pending_p_vals)}\\}}$ "
                        f"have $<\\!3$ finished seeds and are flagged with $\\dagger$.")

    body = (
        "% Auto-generated by agent_reports/make_psweep_analysis.py\n"
        f"% Source: W\\&B tag {tag}\n"
        f"% Scope: {scope}\n"
        f"% Generated: {datetime.utcnow().isoformat(timespec='seconds')}Z\n"
        "\\paragraph{What is the right $p_{\\mathrm{counterfactual}}$?}\n"
        "We sweep the VLM--CF mixing weight "
        "$p_{\\mathrm{counterfactual}} \\in \\{0.00, 0.10, 0.25, 0.50, 0.75, 1.00\\}$ "
        "on FetchPickAndPlace-v4 (3 seeds $\\times$ 500k steps; identical "
        "Sonnet-4.5 \\texttt{achieved\\_goal} VLM generator across all cells; "
        f"see Fig.~\\ref{{fig:psweep}}).  {scope.capitalize()}: "
        f"{inline_results}.  "
        f"The best mean success rate is observed at "
        f"$p\\!=\\!{best['p_float']:.2f}$ "
        f"(${best['mean_sr']:.2f}\\pm{best['se_sr']:.2f}$), versus "
        f"${worst['mean_sr']:.2f}\\pm{worst['se_sr']:.2f}$ at "
        f"$p\\!=\\!{worst['p_float']:.2f}$.  "
        "The $p\\!=\\!0$ recovery cell coincides with the HER-only baseline by construction, "
        "providing an internal consistency check on the mixing implementation.  "
        f"{pending_note}\n"
    )
    out_path.write_text(body)
    print(f"[psweep] wrote {out_path}")


# --- CLI -------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default=DEFAULT_TAG, help="W&B tag filter")
    ap.add_argument("--dry-run", action="store_true",
                    help="Skip W&B query; just confirm script imports cleanly.")
    args = ap.parse_args()

    here = pathlib.Path(__file__).parent
    figs_dir = here / "figs"

    if args.dry_run:
        print("[psweep] --dry-run: skipping W&B query.")
        # Synthesize empty table to verify the rest of the pipeline.
        table = {p: {} for p in P_TOKENS}
        rows = summarize(table)
        write_table_md(rows, here / "_psweep_results.md", args.tag)
        make_bar_chart(rows, figs_dir, args.tag)
        write_paragraph_tex(rows, here / "_psweep_paragraph.tex", args.tag)
        print("[psweep] dry-run OK.")
        return 0

    try:
        table = fetch_psweep_runs(args.tag)
    except Exception as e:
        print(f"[psweep] W&B query failed: {e!r}", file=sys.stderr)
        print("[psweep] exiting 0 (graceful — caller can retry later).")
        return 0

    rows = summarize(table)
    write_table_md(rows, here / "_psweep_results.md", args.tag)
    make_bar_chart(rows, figs_dir, args.tag)
    write_paragraph_tex(rows, here / "_psweep_paragraph.tex", args.tag)

    n_complete = sum(1 for r in rows if r["n_finished"] == 3)
    print(f"[psweep] DONE.  Fully-complete cells: {n_complete}/{len(P_TOKENS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
