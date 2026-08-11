# Architecture

The package is a small, single-responsibility pipeline. Data flows in one
direction: config declares what is scored, IO reads the run of record, the
metric modules compute per-axis results, aggregation assembles them, and the
macro / figure / verify layers consume the assembled results.

```
config  ──┐
          ├─▶ io ──▶ scoring ─────┐
          │         degradation ──┤
          │         latency ──────┴─▶ aggregate ──┬─▶ macros ──▶ verify
          └──────────────────────────────────────┴─▶ figure
```

| Module | Responsibility |
|---|---|
| `config` | engine roster, axes, degradation order, protocol constants; resolves `$OCR_BENCH_DATA` |
| `scoring` | FVR / NED primitives: normalization, Levenshtein, Wilson, seeded bootstrap, date-aware candidates |
| `bootstrap` | four paired document-level bootstraps (IDs/FORMS FVR diffs, HYB NED% diff) from the committed arrays free of personally identifiable information (PII) |
| `mineru_ids` | recompute MinerU's IDs FVR + Wilson CI from the committed PII-free single-engine hit array (the Brazilian identity-document dataset BRIDP is never redistributed) |
| `io` | read per-document prediction/gold pairs and latency manifests from the run of record |
| `degradation` | group HYB pages by DocCreator type and report per-type mean NED% |
| `latency` | per-page median latency (recomputed from manifests for GPU engines; constants for CPU engines) |
| `aggregate` | score every engine on every axis into the consolidated results dict |
| `macros` | render the data-driven LaTeX `\newcommand` values from the consolidated results |
| `verify` | parse the paper reference macros and assert the regenerated values match |
| `figure` | redraw `fig_frontier` (recall vs latency, Pareto frontier); optional matplotlib |
| `cli` | console entry point: `score`, `macros`, `matrix`, `figure`, `reproduce` |

## Design choices

- **No hardcoded host paths.** The data root is `$OCR_BENCH_DATA` or `<repo>/data`;
  the from-scratch script reads `$WORK_DIR`, `$HF_CACHE`, `$VLLM_IMG`.
- **The run of record is the input, not the build pipeline.** The dataset
  construction and model serving are documented (`docs/PROTOCOL.md`,
  `docs/DATASETS.md`) but not runnable code a reviewer needs; the committed
  per-engine outputs make every number reproducible offline.
- **Byte-faithful metrics.** The scorers reproduce the original harness exactly;
  rapidfuzz only swaps the Levenshtein backend (same integer distance, pinned by
  a test) for speed on the long literary NED pages.
- **One assertion gates the Reproducible seal.** `ocr-bench reproduce` compares
  every regenerated macro to the paper reference, exact on point estimates and
  within a stated tolerance on CI bounds (see `docs/PROTOCOL.md`).
