# Measurement protocol

This document records how the run of record was produced and exactly how each
reported number is computed, so the no-GPU reproduction is auditable.

## Metrics

- **Field-value recall (FVR)**: forms, identity documents, English control. A
  gold field value counts as recovered iff its alphanumeric-normalized form is a
  substring of the alphanumeric-normalized transcription. Reported as the micro
  proportion (recovered / total gold values) with a 95% Wilson interval.
  - Identity documents use **date-format-aware** matching: the identity gold stores
    dates as `YYYY-MM-DD` while the cards print `DD/MM/YYYY`, so an ISO gold date
    matches if any of its printed-format variants is a substring. Gold values of
    length <= 1 are dropped (a single character is recovered by chance). The 50
    identity images yield **354** scored fields.
  - The **excl-degenerate** forms variant drops a form whose normalized
    prediction is shorter than 20 characters (a near-empty transcription) and is
    reported alongside the raw forms FVR.
- **Normalized edit distance (NED)**: clean Portuguese prose (RIB) and degraded
  scans (HYB). `NED% = (1 - min(lev(norm(pred), norm(gold)) / max(len(norm(gold)), 1), 1)) * 100`
  with NFC + lowercase + whitespace-collapse normalization. Reported as the mean
  over per-document NED% with a deterministic seeded bootstrap 95% interval.
  - HYB is also reported per degradation type: each page name encodes its
    DocCreator degradation (`pageNNN_<Type>_<idx>.png`); pages are grouped into
    the eight types (28 pages each) and the mean NED% is reported per group.

## Significance tests (paired document-level bootstrap)

Four head-to-head claims carry a **paired, clustered bootstrap** of the axis difference.
Each resamples the scored units (documents for FVR, pages for NED%) with replacement
`B = 10000` times (seed `20260609`), recomputes the per-resample axis value of each engine,
and reports the 95% **percentile** CI of the difference (A − B). For FVR the per-unit pair
is the binary hit `[a_hit, b_hit]` (each `0/1`, from the exact date-aware substring rule
above); for NED% it is the per-page `[a_ned, b_ned]` value pair. Only the integers/floats
are committed (PII-free: no field value, transcription or gold text); the per-field match
and per-page NED were applied once on the GPU host that holds the raw data.

| Axis | A vs B | Marginals | Diff | 95% CI | Excl. 0 | Array | Macros |
| --- | --- | --- | --- | --- | --- | --- | --- |
| IDs FVR | Surya vs DeepSeek-OCR | 0.921 / 0.864 | **+0.057** | [0.023, 0.089] | yes | `ids_pair_hits.json` | `\idsPair{Surya,DeepSeek,Diff,Lo,Hi}` |
| FORMS FVR | Qwen2.5-VL vs GLM-OCR | 0.970 / 0.965 | **+0.005** | [-0.010, 0.019] | **no** | `forms_pair_hits.json` | `\formsPair{Diff,Lo,Hi}` |
| IDs FVR | Surya vs RapidOCR | 0.921 / 0.870 | **+0.051** | [0.023, 0.079] | yes | `ids_pair_hits_surya_rapidocr.json` | `\idsPairRapid{Diff,Lo,Hi}` |
| HYB NED% | Qwen2.5-VL vs Surya | 97.5 / 93.9 | **+3.6** | [1.9, 5.6] | yes | `hyb_pair_ned.json` | `\hybPair{Diff,Lo,Hi}` |

The FORMS pair is a **statistical tie**: the CI straddles 0, so the two best VLMs are
indistinguishable on Brazilian-forms FVR. Because every resampling is recomputed from the
committed array with a fixed seed, each point estimate and **both CI bounds reproduce
exactly** (no tolerance), unlike the per-engine Wilson/NED bounds below. FVR diffs are
asserted to 3 dp, the NED diff to 1 dp, and CI bounds to the paper's printed precision. All
14 paired-bootstrap macros are asserted by `ocr-bench reproduce`.

## Determinism

- Bootstrap: `B = 10000` resamples, seed `20260609`, percentile interval over
  per-document means (per-engine NED CIs) or over the per-unit difference (the four
  paired tests). The seed and `B` match the original harness. The paired bootstraps
  are recomputed from the committed arrays, so they reproduce **exactly**; the
  per-engine NED CIs are reproducible up to the resampling **order**.
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

### MinerU on the IDs / RIB / HYB axes (from-scratch driver)

MinerU was initially run on forms only; it was later scored on the three extra
axes (identity documents, clean prose, degraded scans) with the **same** scorers
as every other engine, so its cells are directly comparable. The from-scratch
driver `run_mineru_axes.py` serves `opendatalab/MinerU2.5-2509-1.2B` once (with
the two-step `mineru_vl_utils:MinerULogitsProcessor`) and transcribes the BRID
(IDs), ESTER-Pt RIB and ESTER-Pt HYB pages, writing one `<img>.mineru.txt` per
page next to the inputs plus a `_run50_mineru_*.json` latency manifest. The
companion aggregator `score_mineru_extra.py` then re-uses the existing axis
scorers verbatim: `score_fvr50_axis_final.py` for the date-aware IDs FVR (micro
+ 95% Wilson), `score_ned_tesseract.py` for the RIB and HYB mean NED% (seeded
bootstrap CI, `B = 10000`, seed `20260609`) and `--by-degradation` for the
eight-way HYB breakdown, and records the IDs median seconds/page. The reviewer
does **not** need this GPU path: the resulting RIB/HYB `<img>.mineru.txt` outputs
are committed under the already-redistributed ESTER-Pt data (CC BY 4.0) and
re-scored live, and a PII-free per-field IDs hit array (`data/ids_mineru_hits.json`,
0/1 per scored field, no BRID text) lets the no-GPU path regenerate MinerU's IDs
FVR + Wilson CI offline. The 19 ID cards that produced empty MinerU output are
scored as genuine zeros (already 0 in the committed hit array).
