#!/usr/bin/env bash
# Pre-flight verification before going to bed. Run this at 23:00ish.
# Tells you exactly what is and isn't running. Exits 0 if you're safe to sleep.
set -u

REPO="/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185"
PASS=0
FAIL=0
WARN=0

green() { printf '\033[32m%s\033[0m\n' "$*"; }
red()   { printf '\033[31m%s\033[0m\n' "$*"; }
amber() { printf '\033[33m%s\033[0m\n' "$*"; }

check() {
    local desc="$1" cmd="$2"
    printf "  %-55s " "$desc"
    if eval "$cmd" >/dev/null 2>&1; then
        green "PASS"
        PASS=$((PASS+1))
        return 0
    else
        red "FAIL"
        FAIL=$((FAIL+1))
        return 1
    fi
}

warn() {
    local desc="$1" cmd="$2"
    printf "  %-55s " "$desc"
    if eval "$cmd" >/dev/null 2>&1; then
        green "OK"
    else
        amber "WARN"
        WARN=$((WARN+1))
    fi
}

echo
echo "=== Overnight pre-flight check ($(date '+%Y-%m-%d %H:%M:%S %Z')) ==="
echo

echo "Critical (must PASS):"
check "PATHC-LEAD agent's orchestrator script exists" "[ -f $REPO/scripts/path_c_orchestrator.py ]"
check "Orchestrator process is running"               "pgrep -f path_c_orchestrator"
check "Watchdog process is running"                   "pgrep -f overnight_watchdog.sh"
check "Local GPU has at least one training process"   "[ \$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits) -gt 1000 ]"
check "At least one Phase 1 W&B run exists"           "cd $REPO && source .venv/bin/activate && python -c \"import wandb; api=wandb.Api(); runs=list(api.runs('d-grant-uc-berkeley/RL_project', filters={'tags':{'\\\$in':['path_c_overnight_2026-05-11']}})); exit(0 if len(runs)>0 else 1)\""
check "configs/oracle_cf.yaml exists"                 "[ -f $REPO/configs/oracle_cf.yaml ]"
check "NeurIPS .sty file is on disk"                  "[ -f $REPO/agent_reports/paper/neurips_2024.sty ]"
check "Latest NeurIPS PDF exists"                     "[ -f $REPO/agent_reports/9pm_presentation.pdf ]"
check "Visual quality gate script exists"             "[ -x $REPO/scripts/visual_quality_gate.py ]"
echo

echo "Important (should PASS but recoverable):"
warn "OpenAI key auto-exported on new shells"         "grep -q OPENAI_API_KEY ~/.zshrc"
warn "Phase 1 has at least 2 jobs running"            "[ \$(pgrep -fc 'python.*train.py') -ge 2 ]"
warn "Watchdog log shows recent activity (<10 min)"   "[ \$(find ~/.local/state/overnight_watchdog.log -mmin -10 2>/dev/null | wc -l) -gt 0 ]"
warn "NeurIPS paper passes visual quality gate"       "python $REPO/scripts/visual_quality_gate.py $REPO/agent_reports/9pm_presentation.pdf"
warn "agent_reports/PATHC-LEAD_handoff.md exists"     "[ -f $REPO/agent_reports/PATHC-LEAD_handoff.md ]"
echo

echo "Power/session (do NOT skip):"
echo "  Disable sleep:"
echo "    gsettings set org.gnome.desktop.session idle-delay 0"
echo "    systemctl --user mask sleep.target suspend.target hibernate.target hybrid-sleep.target"
echo "  Plug in laptop. Leave this terminal open with the Claude Code session running."
echo

echo "=== Summary ==="
echo "  Critical PASS: $PASS"
echo "  Critical FAIL: $FAIL"
echo "  Warnings:      $WARN"
echo

if [ "$FAIL" -eq 0 ]; then
    green "READY TO SLEEP. Watchdog + orchestrator + cron will run overnight."
    echo
    echo "Morning routine:"
    echo "  1. Wake ~07:00 PDT. Look for agent_reports/_MORNING_READY.md (or _MORNING_FALLBACK_2026-05-12.md if first report failed)."
    echo "  2. Check agent_reports/MORNING_REPORT_2026-05-12.md for the KILL-OR-COMMIT verdict."
    echo "  3. scp commands will be in agent_reports/MORNING_SCP_COMMANDS.md."
    echo
    exit 0
else
    red "NOT READY. Fix the FAIL items above before sleeping."
    echo
    echo "Likely culprits:"
    echo "  - PATHC-LEAD agent still running (Stage 1-3 typically 30-60 min). Wait 15 min, re-run."
    echo "  - NIPS-PAPER agent still running. Wait similarly."
    echo "  - If both LLM agents are done but training isn't, check ~/.local/state/path_c_orchestrator.log"
    exit 1
fi
