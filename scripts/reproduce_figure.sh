#!/usr/bin/env bash
# Regenerate fig_frontier.pdf (field-value recall vs processing time, forms and
# IDs panels with the Pareto frontier) from the committed run of record. Needs
# the optional [figure] extra (matplotlib).
#
# Usage: ./scripts/reproduce_figure.sh
# Wall clock: ~1 min (scoring) + a few seconds to draw.
set -euo pipefail
cd "$(dirname "$0")/.."

uv sync --extra figure
uv run ocr-bench figure
echo "wrote results/fig_frontier.pdf"
