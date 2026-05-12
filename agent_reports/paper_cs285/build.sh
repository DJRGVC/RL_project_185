#!/bin/bash
# Build script for CS 285 final-project paper variant.
# Usage: bash build.sh
# NOTE: This is the CS 285 submission variant of the NeurIPS paper.
# Do NOT use this to overwrite the NeurIPS PDF (../paper/main.pdf).
set -e
cd "$(dirname "$0")"
pdflatex -interaction=nonstopmode main.tex >build.log 2>&1 || true
bibtex main >>build.log 2>&1 || true
pdflatex -interaction=nonstopmode main.tex >>build.log 2>&1 || true
pdflatex -interaction=nonstopmode main.tex >>build.log 2>&1 || true
if [ -f main.pdf ]; then
  cp main.pdf ../cs285_final_paper.pdf
  echo "Built: agent_reports/paper_cs285/main.pdf -> agent_reports/cs285_final_paper.pdf"
else
  echo "Build FAILED. See agent_reports/paper_cs285/build.log"
  tail -50 build.log
  exit 1
fi
