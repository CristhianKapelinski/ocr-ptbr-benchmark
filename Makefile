# =============================================================================
# Reading Brazil -- OCR PT-BR benchmark Makefile
# =============================================================================
# Modular entry points for the two reproduce paths. Each target is one line that
# invokes the existing script or CLI; nothing is duplicated here.
#
#   Path A (no GPU, one command): make reproduce
#     re-scores the committed run of record, regenerates and ASSERTS the LaTeX
#     macros against the paper reference, prints the degradation matrix and every
#     data-driven paper table (Tables 3-5).
#   Path B (GPU, gated):          make from-scratch
#     rebuilds the per-engine outputs from the models, then runs path A.
# =============================================================================

.PHONY: help reproduce tables matrix macros score figure from-scratch test lint all

# Default target
help:
	@echo "Reading Brazil -- OCR PT-BR benchmark"
	@echo "====================================="
	@echo ""
	@echo "Reproduce (no GPU, from pre-computed results):"
	@echo "  make reproduce      Re-score, regenerate + ASSERT macros, print matrix + all tables"
	@echo "  make tables         Print the data-driven tables (paper Tables 3-5) from the committed results"
	@echo "  make matrix         Print the per-degradation NED matrix (HYB axis)"
	@echo "  make macros         Regenerate the data-driven LaTeX macros"
	@echo "  make score          Score the run of record -> results/consolidated_results.json"
	@echo "  make figure         Regenerate fig_frontier.pdf (adds the [figure] extra)"
	@echo ""
	@echo "From scratch (GPU, gated):"
	@echo "  make from-scratch   Rebuild per-engine outputs on a CUDA GPU, then reproduce"
	@echo ""
	@echo "Development:"
	@echo "  make test           Run the unit + integration tests (uv run pytest)"
	@echo "  make lint           Run ruff over src and tests"
	@echo "  make all            reproduce + tables + test"

# =============================================================================
# Path A -- reproduce from pre-computed results (no GPU)
# =============================================================================

reproduce:
	./scripts/reproduce_from_results.sh

tables:
	uv run ocr-bench tables

matrix:
	uv run ocr-bench matrix

macros:
	uv run ocr-bench macros

score:
	uv run ocr-bench score

figure:
	./scripts/reproduce_figure.sh

# =============================================================================
# Path B -- regenerate the outputs from scratch (GPU, gated)
# =============================================================================

from-scratch:
	./scripts/run_from_scratch.sh

# =============================================================================
# Development
# =============================================================================

test:
	uv run pytest

lint:
	uv run ruff check src tests

all: reproduce tables test
	@echo "All done: reproduced, emitted every table, and tests passed."
