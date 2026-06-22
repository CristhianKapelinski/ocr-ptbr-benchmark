# Measurement protocol

This document records how the run of record was produced and exactly how each
reported number is computed, so the no-GPU reproduction is auditable.

## Metrics

- **Field-value recall (FVR)** — forms, identity documents, English control. A
  gold field value counts as recovered iff its alphanumeric-normalized form is a
  substring of the alphanumeric-normalized transcription. Reported as the micro
  proportion (recovered / total gold values) with a 95% Wilson interval.
  - Identity documents use **date-format-aware** matching: BRIDP gold stores
    dates as `YYYY-MM-DD` while the cards print `DD/MM/YYYY`, so an ISO gold date
    matches if any of its printed-format variants is a substring. Gold values of
    length <= 1 are dropped (a single character is recovered by chance). The 50
    identity images yield **354** scored fields.
  - The **excl-degenerate** forms variant drops a form whose normalized
    prediction is shorter than 20 characters (a near-empty transcription) and is
    reported alongside the raw forms FVR.
- **Normalized edit distance (NED)** — clean Portuguese prose (RIB) and degraded
  scans (HYB). `NED% = (1 - min(lev(norm(pred), norm(gold)) / max(len(norm(gold)), 1), 1)) * 100`
  with NFC + lowercase + whitespace-collapse normalization. Reported as the mean
  over per-document NED% with a deterministic seeded bootstrap 95% interval.
  - HYB is also reported per degradation type: each page name encodes its
    DocCreator degradation (`pageNNN_<Type>_<idx>.png`); pages are grouped into
    the eight types (28 pages each) and the mean NED% is reported per group.

## IDs significance test (paired document-level bootstrap)

To establish that Surya's identity-document FVR lead over the best vision-language
model (DeepSeek-OCR) is statistically real, the IDs axis carries a **paired,
clustered (document-level) bootstrap** of the FVR difference:

- For every scored IDs gold field, the per-field hit pair `[surya_hit, deepseek_hit]`
  (each `0/1`, from the exact date-aware substring rule above) is recorded with its
  source-document index. Only the integers are committed, in `data/ids_pair_hits.json`
  (PII-free: no field value, transcription or gold text); the per-field match was applied
  once on the GPU host that holds the raw BRIDP data.
- Resample the **50 documents** with replacement `B = 10000` times (seed `20260609`).
  On each resample, recompute the micro-averaged FVR of each engine over the resampled
  documents and take the difference (Surya minus DeepSeek-OCR). The 95% **percentile**
  CI of that resampled difference is reported.
- Result: marginals Surya **0.921** / DeepSeek-OCR **0.864**, point lead **+0.057**,
  95% CI **[0.023, 0.089]**, which **excludes 0** (one-sided empirical p < 0.001). Because
  the resampling is recomputed from the committed hit array with a fixed seed, the point
  lead and **both CI bounds reproduce exactly** (no tolerance), unlike the per-engine
  Wilson/NED bounds below. The macros `\idsPairSurya`, `\idsPairDeepSeek`, `\idsPairDiff`,
  `\idsPairLo`, `\idsPairHi` are asserted by `ocr-bench reproduce`.

## Determinism

- Bootstrap: `B = 10000` resamples, seed `20260609`, percentile interval over
  per-document means (per-engine NED CIs) or over the per-document FVR difference
  (the paired IDs test). The seed and `B` match the original harness. The paired
  IDs bootstrap is recomputed from the committed hit array, so it reproduces
  **exactly**; the per-engine NED CIs are reproducible up to the resampling **order**.
- The Levenshtein distance is computed with rapidfuzz's C backend, which returns
  the identical integer distance to the bundled pure-stdlib reference
  (`scoring._levenshtein_py`); a unit test pins this equivalence.

## Reproduction tolerance

Point estimates (every FVR, NED mean, latency median, and per-degradation cell)
reproduce **exactly** at the paper's printed precision. Confidence-interval
bounds are checked within a stated tolerance because the original consolidated
results did not record the exact bootstrap resampling order, and the FVR Wilson
bounds carry a last-digit rounding difference from a two-step rounding in the
original consolidation:

- NED CI bounds (`rib*Lo/Hi`, `hyb*Lo/Hi`): tolerance 0.15 percentage points.
- FVR CI bounds (`forms*/ids*/en* Lo/Hi`): tolerance 0.0011.

The assertion in `ocr-bench reproduce` enforces exact point estimates and these
CI tolerances; any larger deviation is a reproduction failure.

## Latency

- GPU-served engines (the eight vision-language models and Surya) are timed per
  page; the median seconds/page is **recomputed offline** from the committed
  `_run*.json` manifests (each a list of `{img, sec, err, ...}` records; the
  median is over the pages with `err is None`). Forms uses the `_run50_*.json`
  manifest; Surya is named `_run_surya.json`; the RIB/HYB Qwen2.5-VL manifest
  carries a `_txt` suffix. These reproduce the paper's latency cells exactly.
- Classical CPU pipelines (Tesseract, EasyOCR, docTR, RapidOCR, PaddleOCR) were
  timed once load-once on the reference machine; their measured medians are
  committed as constants in `data/cost/_classical_latency.json` because their
  per-page run manifests are not part of the run of record.

## From-scratch generation (optional, GPU)

The vision-language models were served one at a time on a single 16 GB card via
the pinned vLLM image `vllm/vllm-openai:v0.22.1-cu129-ubuntu2404` with:

```
--gpu-memory-utilization 0.92 --max-model-len 16384
--mm-processor-kwargs {"max_pixels":4000000}
--limit-mm-per-prompt {"image":1} --max-num-seqs 2 --trust-remote-code
```

and greedy decoding (temperature 0) at each engine's vendor defaults. Two
engines (GLM-OCR, Qwen2.5-VL) run in fp8 to fit the card. DeepSeek-OCR overrides
`--max-model-len 8192` (its `max_position_embeddings`). MinerU is a two-step
parse and requires its `mineru_vl_utils:MinerULogitsProcessor`. Each engine
receives the page image and a single transcription instruction and returns a
full-page transcription. The classical pipelines run on CPU and Surya on GPU,
each at its default backend. `scripts/run_from_scratch.sh` documents the roster
and hands off to the no-GPU scoring path once outputs exist.
