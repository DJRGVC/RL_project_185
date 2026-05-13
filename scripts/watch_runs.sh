#!/usr/bin/env bash
# ETA-forward pipeline dashboard. Run with:
#   watch -n 60 -c bash ~/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/scripts/watch_runs.sh
# Refreshes every 60s.
REPO="/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185"
cd "$REPO" 2>/dev/null
source .venv/bin/activate 2>/dev/null

cyan()   { printf '\033[36m%s\033[0m\n' "$*"; }
green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
red()    { printf '\033[31m%s\033[0m\n' "$*"; }
dim()    { printf '\033[2m%s\033[0m\n' "$*"; }
white()  { printf '\033[97m%s\033[0m\n' "$*"; }

cyan "═══ $(date '+%Y-%m-%d %H:%M:%S %Z') — Path C pipeline ═══"
echo

# Get live data via Python (fast batched query)
python3 << 'PY' 2>/dev/null
import wandb, datetime, sys, time
from datetime import timedelta

api = wandb.Api()
now = datetime.datetime.utcnow()

def fmt_eta(seconds):
    if seconds < 0:
        return "DONE"
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds/60)}m"
    if seconds < 86400:
        return f"{int(seconds/3600)}h{int((seconds%3600)/60)}m"
    return f"{int(seconds/86400)}d{int((seconds%86400)/3600)}h"

def fmt_pdt(dt):
    pdt = dt - timedelta(hours=7)  # UTC → PDT
    return pdt.strftime('%H:%M')

# ───────────── NOW: in-flight runs ─────────────
print("\033[33m▌ NOW (in-flight)\033[0m")

# Find all running runs created today
runs = list(api.runs('d-grant-uc-berkeley/RL_project',
    filters={'created_at': {'$gte': '2026-05-12T00:00:00Z'}}, per_page=100))
active = [r for r in runs if r.state == 'running']

if not active:
    print("  (no active W&B runs)")
else:
    # Group by experiment "bucket"
    buckets = {}
    for r in active:
        name = r.name or ''
        if 'oracle_cf_1m_pnp' in name or 'ocf_pnp_1m' in name:
            buckets.setdefault('Oracle-CF 1M PnP', []).append(r)
        elif name.startswith('path_c_vlm_cf_pp_'):
            buckets.setdefault('Phase2 vlm_cf PnP', []).append(r)
        elif name.startswith('path_c_vlm_cf_'):
            buckets.setdefault('Phase2 vlm_cf other', []).append(r)
        elif name.startswith('path_c_vlm_vcf_pp_'):
            buckets.setdefault('Phase2 verified_cf PnP', []).append(r)
        elif name.startswith('path_c_vlm_vcf_'):
            buckets.setdefault('Phase2 verified_cf other', []).append(r)
        elif 'psweep' in name or 'p_counterfactual' in name:
            buckets.setdefault('P-counterfactual sweep', []).append(r)
        elif 'path_c_kill_ocf_sld' in name:
            buckets.setdefault('Oracle-CF Slide 250k', []).append(r)
        else:
            buckets.setdefault('Other', []).append(r)

    for label, rs in buckets.items():
        steps = []
        srs = []
        targets = []
        for r in rs:
            step = r.summary.get('global_step', 0)
            sr = r.summary.get('eval/success_rate', r.summary.get('charts/eval/success_rate', 0))
            cfg_steps = r.config.get('training', {}).get('total_steps') or r.config.get('total_steps') or 500_000
            steps.append(step)
            srs.append(float(sr) if sr else 0.0)
            targets.append(cfg_steps)
        # ETA estimate: assume linear pace based on the lead run
        avg_step = sum(steps) / max(len(steps), 1)
        avg_target = sum(targets) / max(len(targets), 1)
        pct = 100 * avg_step / avg_target if avg_target else 0
        # Use creation time to estimate steps/sec
        oldest_created = min(r.created_at for r in rs)
        oldest_dt = datetime.datetime.fromisoformat(oldest_created.replace('Z',''))
        elapsed_s = (now - oldest_dt).total_seconds()
        steps_per_s = max(steps) / max(elapsed_s, 1) if elapsed_s > 0 else 1
        remaining = max(0, max(targets) - max(steps)) if steps else avg_target
        eta_s = remaining / max(steps_per_s, 0.1)
        finish_pdt = fmt_pdt(now + timedelta(seconds=eta_s))
        sr_mean = sum(srs) / max(len(srs), 1)
        print(f"  \033[32m{label:30s}\033[0m  n={len(rs)} step≈{int(avg_step/1000)}k/{int(avg_target/1000)}k ({pct:.0f}%) SR̄={sr_mean:.2f} → finish ~{finish_pdt} PDT (eta {fmt_eta(eta_s)})")

# ───────────── NEXT: queued / awaiting ─────────────
print()
print("\033[33m▌ NEXT (queued, in dependency order)\033[0m")

import os
psweep_launched = os.path.exists('agent_reports/_PSWEEP_LAUNCHED.md')
psweep_running = any('psweep' in (r.name or '') for r in runs)
if not psweep_launched and not psweep_running:
    # Check if watcher is alive
    import subprocess
    res = subprocess.run(['pgrep', '-f', 'launch_psweep_when_ready'], capture_output=True, text=True)
    if res.stdout.strip():
        # Watcher alive
        # Estimate trigger: when last Phase 2 vcf finishes
        vcf_runs = [r for r in active if 'vcf' in (r.name or '')]
        if vcf_runs:
            # ETA = max ETA among vcf runs
            slowest_eta = 0
            for r in vcf_runs:
                step = r.summary.get('global_step', 0)
                target = r.config.get('training', {}).get('total_steps') or 500_000
                created = datetime.datetime.fromisoformat(r.created_at.replace('Z',''))
                elapsed_s = (now - created).total_seconds()
                rate = step / max(elapsed_s, 1) if elapsed_s > 0 else 1
                eta = (target - step) / max(rate, 0.1)
                slowest_eta = max(slowest_eta, eta)
            launch_t = now + timedelta(seconds=slowest_eta)
            sweep_finish = launch_t + timedelta(hours=6)  # 18 runs at ~5hr each on 10-cap = ~6hr serial batches
            print(f"  \033[36mp_counterfactual sweep (18 runs)\033[0m   waits for vcf clearance → launch ~{fmt_pdt(launch_t)} PDT, finish ~{fmt_pdt(sweep_finish)} PDT")
        else:
            print(f"  \033[36mp_counterfactual sweep\033[0m   watcher alive, no clear ETA yet")
    else:
        print(f"  \033[31mp_counterfactual watcher NOT alive — manual launch may be required\033[0m")
else:
    print(f"  \033[2m(p-sweep already launched/running)\033[0m")

# Manual queue (designed but not auto-launching)
print(f"  \033[2mAfter p-sweep: 2x2 numeric prompt ablation (4 configs × 3 seeds × 500k, ~$200, ~6hr)\033[0m")
print(f"  \033[2mAfter p-sweep: HER+PER baseline + Sharony VLM-RB (canonical comparators, ~$150, ~6hr)\033[0m")

# ───────────── DONE: recent completions (last 4 hr) ─────────────
print()
print("\033[33m▌ DONE (last 4h, key results)\033[0m")
recent_finished = []
for r in runs:
    if r.state != 'finished':
        continue
    try:
        # Use heartbeat or summary's max recent timestamp
        ht = getattr(r, 'heartbeat_at', None) or r.created_at
        ht_dt = datetime.datetime.fromisoformat(ht.replace('Z','')) if isinstance(ht, str) else ht
        if (now - ht_dt).total_seconds() < 14400:  # 4hr
            recent_finished.append((ht_dt, r))
    except Exception:
        continue
recent_finished.sort(key=lambda x: x[0], reverse=True)

# Group recent finishes
finished_buckets = {}
for ht_dt, r in recent_finished:
    name = r.name or ''
    sr = r.summary.get('eval/success_rate', r.summary.get('charts/eval/success_rate', 0))
    if 'oracle_cf_1m' in name or 'ocf_pnp_1m' in name:
        finished_buckets.setdefault('OCF 1M PnP', []).append((name.split('_seed')[0][-3:], float(sr) if sr else 0))
    elif 'cf_push' in name and 'vcf' not in name:
        finished_buckets.setdefault('vlm_cf Push', []).append((name.split('_seed')[0][-3:], float(sr) if sr else 0))
    elif 'cf_sld' in name and 'vcf' not in name:
        finished_buckets.setdefault('vlm_cf Slide', []).append((name.split('_seed')[0][-3:], float(sr) if sr else 0))
    elif 'cf_pp' in name and 'vcf' not in name:
        finished_buckets.setdefault('vlm_cf PnP', []).append((name.split('_seed')[0][-3:], float(sr) if sr else 0))

for label, results in finished_buckets.items():
    seed_srs = ', '.join(f's{s}={sr:.2f}' for s, sr in results)
    mean = sum(sr for _, sr in results) / len(results)
    color = '\033[32m' if mean > 0.4 else '\033[33m' if mean > 0.2 else '\033[31m'
    print(f"  {color}{label:20s}\033[0m  mean={mean:.2f}  ({seed_srs})")

if not finished_buckets:
    print("  (no major completions in last 4h)")

PY

echo

# ───────────── ALERTS ─────────────
NEW_ALERTS=$(find agent_reports -name '_*_DEAD.md' -o -name '_*FAILED.md' -o -name '_*STALLED.md' -newer ~/.local/state/overnight_watchdog.log 2>/dev/null | head -3)
if [ -n "$NEW_ALERTS" ]; then
    yellow "▌ ALERTS (new, since watchdog start)"
    echo "$NEW_ALERTS" | sed 's/^/  /'
    red "  ⚠ Run cat on any of these to see details"
fi

# Quick watchdog liveness
WD_ALIVE=$(pgrep -fc 'overnight_watchdog|launch_psweep_when_ready' 2>/dev/null)
if [ "${WD_ALIVE:-0}" -lt 2 ]; then
    red "  ⚠ One or both watchdogs not alive (expected 2: overnight_watchdog + launch_psweep)"
fi

echo
dim "  refresh:  watch -n 60 -c bash $REPO/scripts/watch_runs.sh"
dim "  one-shot: bash $REPO/scripts/watch_runs.sh"
