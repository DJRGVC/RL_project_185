# Morning SCP Commands — 2026-05-12

Ready-to-paste commands for pulling the morning artifacts off the workstation.
Run from your local laptop / phone. Replace `WORKSTATION_HOST` with the SSH host
alias you use (e.g.\ `dgrant-ws`, the IP, or whatever is in your `~/.ssh/config`).

The remote path is
`/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports`.

## Single-file pulls

```bash
# Executive briefing (7 pages, 96 KB)
scp WORKSTATION_HOST:/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/OVERNIGHT_SUMMARY.pdf ./

# Updated paper PDF (35 pages, 532 KB)
scp WORKSTATION_HOST:/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/9pm_presentation.pdf ./

# Updated 16:9 slidedeck (12 slides, 172 KB)
scp WORKSTATION_HOST:/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/9pm_slidedeck.pdf ./

# Morning report (markdown, copy-paste-able)
scp WORKSTATION_HOST:/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/MORNING_REPORT_2026-05-12.md ./

# Headline figure (NeurIPS-style, PNG + PDF)
scp WORKSTATION_HOST:/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/figs/fig_morning_headline.png ./
scp WORKSTATION_HOST:/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/figs/fig_morning_headline.pdf ./
```

## One-shot pull (all four primary deliverables)

```bash
mkdir -p ~/Downloads/rl_project_185_morning_2026-05-12 && \
scp \
  WORKSTATION_HOST:/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/OVERNIGHT_SUMMARY.pdf \
  WORKSTATION_HOST:/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/9pm_presentation.pdf \
  WORKSTATION_HOST:/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/9pm_slidedeck.pdf \
  WORKSTATION_HOST:/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/MORNING_REPORT_2026-05-12.md \
  ~/Downloads/rl_project_185_morning_2026-05-12/
open ~/Downloads/rl_project_185_morning_2026-05-12/OVERNIGHT_SUMMARY.pdf
```

## Recursive pull (everything new under agent_reports)

If you want all the supporting artifacts (figure audits, agent handoffs, training
status reports, etc.) in one go:

```bash
mkdir -p ~/Downloads/rl_project_185_morning_2026-05-12 && \
rsync -av --include='*.pdf' --include='*.md' --include='*.png' \
  --exclude='__pycache__' --exclude='*.aux' --exclude='*.log' \
  WORKSTATION_HOST:/home/daniel-grant/Berkeley/Spring2026/DeepRL/FinalProject/RL_project_185/agent_reports/ \
  ~/Downloads/rl_project_185_morning_2026-05-12/
```

## File sizes (for sanity check before download)

| File | Size | Pages |
|---|---|---|
| `OVERNIGHT_SUMMARY.pdf` | 96 KB | 7 |
| `9pm_presentation.pdf` (paper) | 532 KB | 35 |
| `9pm_slidedeck.pdf` | 172 KB | 12 |
| `MORNING_REPORT_2026-05-12.md` | ~12 KB | n/a |
| `figs/fig_morning_headline.png` | 84 KB | n/a |
| `figs/fig_morning_headline.pdf` | 24 KB | n/a |
