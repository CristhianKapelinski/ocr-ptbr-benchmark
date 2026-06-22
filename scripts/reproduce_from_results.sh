#!/usr/bin/env bash
# Reproduce every paper number AND every paper table from the committed run of
# record (no GPU, no network). Re-scores the per-engine OCR outputs, regenerates
# the LaTeX macros and the per-degradation matrix, ASSERTS the regenerated values
# are identical to the paper's committed reference, then emits all of the paper's
# tables (Tables 1-4) as readable output. Exits non-zero on any mismatch.
#
# Usage: ./scripts/reproduce_from_results.sh
# Wall clock: ~2-4 min on the reference machine (dominated by the seeded
# bootstrap CIs; pure CPU, single thread).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== OCR PT-BR benchmark: reproduce from stored results =="
uv run ocr-bench reproduce

echo
echo "== Per-degradation NED matrix (HYB) =="
uv run ocr-bench matrix

echo
echo "== Paper tables (regenerated from the run of record) =="
uv run ocr-bench tables

echo
echo "== Figure =="
echo "fig_frontier.pdf is reproduced separately with the [figure] extra:"
echo "  make figure    (or ./scripts/reproduce_figure.sh)"
