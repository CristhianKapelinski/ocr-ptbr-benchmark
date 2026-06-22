# Tool: Reading Brazil — a Brazilian-Portuguese OCR cost-versus-precision benchmark

A reproducible scoring harness for the first systematic OCR benchmark that pairs a
Brazilian-Portuguese **accuracy** axis with a local consumer-GPU **cost** axis across
the open OCR wave. It scores **14 engines** (8 vision-language models from 0.9B to 9B,
five purpose-built OCR pipelines, and one specialized engine) on Brazilian forms,
identity documents, clean Portuguese prose, degraded scans, and an English control.
The headline: no class wins outright — an OCR engine (**Surya**, **0.921** field-value
recall on IDs) and a vision-language model (**Qwen2.5-VL**, **0.97** on forms and
**97.53** NED on degraded scans) lead every axis. This repository re-scores the
committed per-engine outputs offline and **asserts** the regenerated numbers are
identical to the paper's.

> **Paper:** "Reading Brazil: A Local Cost-versus-Precision Benchmark" (under review).
> Target venue: SBSeg/SBRC Salão de Ferramentas (artifact track).

**This README is the single self-contained guide a reviewer needs.** The files under
`docs/` (`PROTOCOL.md`, `DATASETS.md`, `ARCHITECTURE.md`) are complementary detail and
are not required to grant the seals.

## README structure

| Section | What it covers |
|---|---|
| [Considered seals](#considered-seals) | why each of the four seals holds |
| [Basic information](#basic-information) | OS, runtime, RAM, disk, GPU |
| [Dependencies](#dependencies) | how the environment and inputs are obtained |
| [Security concerns](#security-concerns) | what runs locally and where data lives |
| [Installation](#installation) | clone + `uv sync` |
| [Minimal test](#minimal-test) | one command, end to end |
| [Experiments](#experiments) | the claims and how to reproduce each |
| [License](#license) | MIT |

## Considered seals

- **Disponível (SeloD):** public repository with an open MIT license and a DOI-able
  archive at camera-ready; everything needed to run is in the repository.
- **Funcional (SeloF):** one command (`./scripts/reproduce_from_results.sh`) scores the
  committed run of record end to end and prints the per-task table and per-degradation
  matrix; unit tests cover the metric logic.
- **Sustentável (SeloS):** packaged `src/` layout, one concern per module, typed public
  functions, pinned dependencies (`pyproject.toml` + committed `uv.lock`), tests and
  lint config; nothing is hardcoded to a host (all paths come from the environment).
- **Reprodutível (SeloR):** the no-GPU path regenerates every paper number from the
  committed per-engine outputs and **asserts** they match the paper's reference macro
  file byte-for-byte at the printed precision; deterministic seeds (bootstrap seed
  `20260609`) make the confidence intervals exactly reproducible.

## Basic information

| | Reference machine |
|---|---|
| OS | Linux x86-64 (Ubuntu 24.04 tested) |
| Runtime | Python >= 3.11, managed with `uv` |
| CPU | AMD Ryzen 7 9700X (8 cores / 16 threads) |
| RAM | 64 GB (the no-GPU path uses < 1 GB) |
| Disk | ~120 MB for the clone (the run of record is ~32 MB) |
| GPU | **none needed** for the reproduce path. The optional from-scratch path needs one NVIDIA RTX 5080 16 GB (or any >= 16 GB CUDA card) |

## Dependencies

The environment is managed with **`uv`**; you never build a virtualenv by hand. The
no-GPU reproduce path has a single runtime dependency, **`rapidfuzz`** (a fast C
Levenshtein backend that returns the identical distance to the bundled pure-stdlib
reference); the figure extra adds **`matplotlib`**. All versions are pinned in
`pyproject.toml` and frozen in the committed `uv.lock`.

The **inputs** are bundled: the committed run of record (`data/`) holds the per-engine
OCR transcriptions, the gold answer sets, and the per-page latency manifests, so the
reviewer downloads nothing. The document **images** are not redistributed (license +
size); see `docs/DATASETS.md` for fetching them, needed only by the from-scratch path.

## Security concerns

- The reproduce path runs entirely **locally and offline**: it reads only the committed
  `data/` directory and writes only under `results/`. No network access, no GPU, no
  external services.
- No credentials or secrets are used or stored. The optional from-scratch path downloads
  open model weights from Hugging Face into a cache directory you choose via `$HF_CACHE`.
- The bundled gold and transcriptions contain only **synthetic or public** document
  content (privacy-synthetic Brazilian IDs, public literary text, benchmark forms); no
  real personal data.

## Installation

```bash
# 1. Clone
git clone <REPO_URL> ocr-ptbr-benchmark
cd ocr-ptbr-benchmark

# 2. Install uv (one line; skip if you already have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Create the pinned environment from uv.lock
uv sync
```

## Minimal test

One command re-scores the committed run of record, regenerates the paper's LaTeX macros,
and asserts they match the paper reference, then prints the per-degradation matrix:

```bash
./scripts/reproduce_from_results.sh
```

Expected tail of the output (the assertion is the proof of reproduction):

```
      OK: all <N> regenerated macros match results_macros.reference.tex

PASS: reproduced the paper's numbers from the committed run of record.
```

followed by the 14-engine x 8-degradation NED matrix. **Expected time: ~30-60 s**
(pure CPU, single thread). A non-zero exit means at least one regenerated number differs
from the paper and the mismatch is printed.

## Experiments

All claims are reproduced from the **same** committed run of record by the single
`reproduce` command; the individual numbers below are fields of the results it writes to
`results/consolidated_results.json`, not separate runs.

### Main claim — no OCR class wins outright; the leaders are document-type dependent

- **Description:** re-scoring the per-engine outputs reproduces the paper's per-task
  accuracy (forms/IDs/EN field-value recall, clean/degraded NED), the cost (latency)
  table, and the per-degradation matrix, and confirms Surya leads identity documents
  (**0.921**) ahead of every vision-language model while Qwen2.5-VL leads forms
  (**0.97**) and degraded scans (**97.53** NED).
- **Execution:**
  ```bash
  ./scripts/reproduce_from_results.sh
  ```
- **Expected time:** ~30-60 s. **Expected resources:** < 1 GB RAM, ~32 MB read, no GPU.
- **Expected result:** `PASS: reproduced the paper's numbers ...` and the printed
  per-degradation matrix. Every data-driven macro in
  `results/results_macros.generated.tex` equals the committed
  `results/results_macros.reference.tex` (the file the paper compiles).

### Supporting claim — the cost frontier figure

- **Description:** regenerate `fig_frontier.pdf` (field-value recall vs median
  processing time, forms and IDs panels, Pareto frontier dashed).
- **Execution:**
  ```bash
  ./scripts/reproduce_figure.sh
  ```
- **Expected time:** ~1 min (adds `matplotlib`). **Expected result:**
  `results/fig_frontier.pdf` with the two-panel frontier plot.

### Optional — regenerate the outputs from scratch (GPU, gated)

- **Description:** rebuild the per-engine transcriptions from the models and documents,
  then score them with the path above. A reviewer does **not** need this.
- **Execution:**
  ```bash
  ./scripts/run_from_scratch.sh
  ```
- **Expected time:** many hours (model downloads + 14 engines x 5 axes). **Expected
  resources:** one >= 16 GB CUDA GPU. See `docs/PROTOCOL.md` for the full serving recipe.

## License

MIT — see [LICENSE](LICENSE).
