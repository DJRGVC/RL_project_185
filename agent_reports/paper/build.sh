#!/bin/bash
# Build script for NeurIPS-style paper.
# Usage: bash build.sh
set -e
cd "$(dirname "$0")"
pdflatex -interaction=nonstopmode main.tex >build.log 2>&1 || true
bibtex main >>build.log 2>&1 || true
pdflatex -interaction=nonstopmode main.tex >>build.log 2>&1 || true
pdflatex -interaction=nonstopmode main.tex >>build.log 2>&1 || true
if [ -f main.pdf ]; then
  cp main.pdf ../9pm_presentation.pdf
  echo "Built: agent_reports/paper/main.pdf -> agent_reports/9pm_presentation.pdf"
else
  echo "Build FAILED. See agent_reports/paper/build.log"
  tail -50 build.log
  exit 1
fi
