#!/usr/bin/env bash
# Reproduce every paper number from the committed run of record (no GPU, no
# network). Re-scores the per-engine OCR outputs, regenerates the LaTeX macros
# and the per-degradation matrix, and ASSERTS the regenerated values are
# identical to the paper's committed reference. Exits non-zero on any mismatch.
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
