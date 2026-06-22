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
- **Reprodutível (SeloR):** the no-GPU path re-scores the committed ESTER-Pt outputs
  live, regenerates the forms/IDs/EN numbers from the committed run of record, and
  recomputes the IDs paired significance test from a committed PII-free hit array, then
  **asserts** every data-driven macro matches the paper's reference macro file at the
  printed precision; deterministic seeds (bootstrap seed `20260609`) make the confidence
  intervals exactly reproducible. No raw PII is needed or present.

## Basic information

| | Reference machine |
|---|---|
| OS | Linux x86-64 (Ubuntu 24.04 tested) |
| Runtime | Python >= 3.11, managed with `uv` |
| CPU | AMD Ryzen 7 9700X (8 cores / 16 threads) |
| RAM | 64 GB (the no-GPU path uses < 1 GB) |
| Disk | ~30 MB for the clone (the committed ESTER-Pt run of record is ~25 MB) |
| GPU | **none needed** for the reproduce path. The optional from-scratch path needs one NVIDIA RTX 5080 16 GB (or any >= 16 GB CUDA card) |

## Dependencies

The environment is managed with **`uv`**; you never build a virtualenv by hand. The
no-GPU reproduce path has a single runtime dependency, **`rapidfuzz`** (a fast C
Levenshtein backend that returns the identical distance to the bundled pure-stdlib
reference); the figure extra adds **`matplotlib`**. All versions are pinned in
`pyproject.toml` and frozen in the committed `uv.lock`.

The **inputs the reviewer needs are bundled**, but only the cleanly redistributable
subset is committed. For licence and privacy reasons (see `data/DATA-LICENSES.md`):

- **Committed (CC BY 4.0, no PII):** the ESTER-Pt RIB/HYB axis under `data/rib` and
  `data/hyb` (reference transcriptions, per-engine outputs, latency manifests). The
  no-GPU path **re-scores** these live.
- **Not redistributed:** the forms (XFUND), identity-document (BRIDP) and
  English-control (FUNSD) raw outputs and gold. Their gold carries
  synthetic-but-realistic PII (names, CPFs, e-mails, addresses, dates of birth) under
  restrictive licences (XFUND CC BY-NC-SA 4.0, FUNSD research-only, BRIDP unstated).
  Their **aggregate scores** are committed as the run of record
  (`results/run_of_record.json`, numbers only); the no-GPU path regenerates and
  **asserts** their macros from that file. These committed scores are the run of
  record for those axes. The IDs significance test additionally ships a PII-free
  per-field hit array (`data/ids_pair_hits.json`: only `0/1` hits and integer
  document indices, no field values) so the paired bootstrap is recomputable too.

The reviewer therefore downloads nothing. The from-scratch path fetches the source
inputs with `scripts/fetch_data.sh`; document **images** are never committed
(licence + size). See `docs/DATASETS.md`.

## Security concerns

- The reproduce path runs entirely **locally and offline**: it reads only the committed
  `data/` directory and `results/run_of_record.json`, and writes only under `results/`.
  No network access, no GPU, no external services.
- **No personal data is committed anywhere.** The committed tree holds only
  public-domain Portuguese literary text (ESTER-Pt, CC BY 4.0) and aggregate numbers
  (latency medians, per-engine scores). The forms/ids/en raw field values — which
  contain synthetic PII (names, CPFs, e-mails, addresses, dates of birth) — are **not**
  redistributed; only their aggregate scores are. The IDs paired-bootstrap input
  (`data/ids_pair_hits.json`) is likewise PII-free: it holds only binary per-field hits
  (`0/1`) and integer document indices, never a field value or transcription. The
  from-scratch path fetches the source inputs (`scripts/fetch_data.sh`) under each
  dataset's own licence.
- No credentials or secrets are used or stored. The optional from-scratch path downloads
  open model weights from Hugging Face into a cache directory you choose via `$HF_CACHE`.

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

- **Description:** re-scoring the committed ESTER-Pt outputs (clean/degraded NED, the
  per-degradation matrix) live, and regenerating the forms/IDs/EN field-value recall and
  cost (latency) table from the committed run of record, reproduces the paper's per-task
  accuracy and confirms Surya leads identity documents
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

### Significance claim — Surya's IDs lead over the best VLM is statistically real

- **Description:** a **paired, document-level (clustered) bootstrap** on the identity-document
  axis confirms that Surya's field-value recall lead over the best vision-language model
  (**DeepSeek-OCR**) is not noise. Resampling the 50 documents with replacement
  `B = 10000` times (seed `20260609`) and recomputing the micro-averaged FVR difference on
  each resample yields a point lead of **+0.057** with a 95% percentile CI of
  **[0.023, 0.089]** that **excludes 0** (marginals: Surya **0.921**, DeepSeek-OCR
  **0.864**). The same `reproduce` command recomputes this from the committed PII-free hit
  array `data/ids_pair_hits.json` (for every scored field, the pair
  `[surya_hit, deepseek_hit]` in `{0,1}` plus an integer document index — no field values,
  transcriptions or gold text) and **asserts** it regenerates `\idsPairDiff=0.057`,
  `\idsPairLo=0.023`, `\idsPairHi=0.089` (with marginals `\idsPairSurya=0.921`,
  `\idsPairDeepSeek=0.864`) exactly.
- **Execution:**
  ```bash
  ./scripts/reproduce_from_results.sh
  ```
- **Expected result:** step `[2/5]` prints
  `Surya 0.921 vs DeepSeek-OCR 0.864; diff 0.057 95% CI [0.023, 0.089] ... excludes 0: True`,
  and the macro assertion in step `[4/5]` covers the five `\idsPair*` macros. A standalone
  check is `uv run pytest tests/test_bootstrap.py`.

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

- **Description:** fetch the source datasets, rebuild the per-engine transcriptions from
  the models and documents, then score them with the path above. A reviewer does **not**
  need this; the no-GPU path reproduces every number offline.
- **Execution:**
  ```bash
  ./scripts/fetch_data.sh        # download XFUND PT, FUNSD, ESTER-Pt (BRIDP: request)
  ./scripts/run_from_scratch.sh  # serve engines, then re-score and assert
  ```
  `fetch_data.sh` is idempotent and sha256-verified; it fetches XFUND (CC BY-NC-SA 4.0),
  FUNSD (research-only) and ESTER-Pt (CC BY 4.0) from source and prints how to request
  BRIDP (no public download). When the raw forms/ids/en data is present, the scorer
  re-scores those axes live instead of reading the committed run of record, so the same
  command reproduces the full run end to end.
- **Expected time:** many hours (model downloads + 14 engines x 5 axes). **Expected
  resources:** one >= 16 GB CUDA GPU. See `docs/PROTOCOL.md` for the full serving recipe.

## License

Code is **MIT** — see [LICENSE](LICENSE). Data has its own terms — see
[data/DATA-LICENSES.md](data/DATA-LICENSES.md): the redistributed ESTER-Pt RIB/HYB run
of record is **CC BY 4.0** (attribute the ESTER-Pt authors); the other datasets are
fetched from source under their own licences (XFUND CC BY-NC-SA 4.0, FUNSD research-only,
BRIDP unstated) and are **not** redistributed here.
