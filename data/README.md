# Run of record

This directory holds the committed run of record the no-GPU reproduce path scores
offline. For license and privacy reasons only the cleanly redistributable subset
is committed here (see `DATA-LICENSES.md`):

- **`rib/`, `hyb/`**: the ESTER-Pt clean and degraded axes (CC BY 4.0,
  public-domain literature, no personally identifiable information (PII)): per-document `*.gold.txt` reference
  transcriptions and the per-engine `*.<engine>.txt` outputs scored against them,
  plus `_run*.json` per-page latency manifests for the GPU-served engines.
- **`cost/_classical_latency.json`**: measured CPU latency medians for the
  classical pipelines (aggregate numbers, no document content).
- **Paired-bootstrap arrays**: PII-free derived inputs for the four document-level
  significance tests; only integers/floats, no field value, transcription or gold
  text. Derived once from the raw outputs on the GPU host; the no-GPU path resamples
  each to regenerate its test (`B=10000`, seed `20260609`):
  - **`ids_pair_hits.json`**: per scored IDs field, the hit pair
    `[surya_hit, deepseek_hit]` (`0/1`) + doc index. Surya +0.057 over DeepSeek-OCR,
    95% CI [0.023, 0.089] (excludes 0).
  - **`forms_pair_hits.json`**: per scored forms field, `[qwen25vl_hit, glmocr_hit]`
    (`0/1`) + doc index. Qwen2.5-VL +0.005 over GLM-OCR, 95% CI [-0.010, 0.019]
    (straddles 0; a statistical tie).
  - **`ids_pair_hits_surya_rapidocr.json`**: per scored IDs field,
    `[surya_hit, rapidocr_hit]` (`0/1`) + doc index. Surya +0.051 over RapidOCR,
    95% CI [0.023, 0.079] (excludes 0).
  - **`hyb_pair_ned.json`**: per HYB page, the `[qwen25vl_ned, surya_ned]` NED% floats
    + doc index. Qwen2.5-VL +3.6 over Surya, 95% CI [1.9, 5.6] (excludes 0).
- **`ids_mineru_hits.json`**: PII-free single-engine IDs hit array for MinerU
  (BRIDP is never redistributed): per scored IDs field, a `[doc_index, hit]` row
  with `hit` 0/1 (date-aware substring match, the same rule as every other engine),
  plus integer metadata (recovered/total, the 19 empty-output cards scored as
  genuine zeros). The no-GPU path re-sums it to regenerate MinerU's IDs FVR
  **0.463**, 95% Wilson CI [0.412, 0.515] (`n=50`, 164/354 fields). No field text.

The **forms (XFUND), identity-document (BRIDP) and English-control (FUNSD)** raw
outputs and gold are **not** committed: their gold carries synthetic PII (names,
CPFs, e-mails, addresses, dates of birth) under restrictive licences. Their
**aggregate scores** are the run of record in `../results/run_of_record.json`
(numbers only), which the reproduce path uses to regenerate and assert their
macros. To rebuild them from scratch, `scripts/fetch_data.sh` downloads the source
inputs (XFUND PT, FUNSD; BRIDP must be requested from its authors). Document
images are never committed (license + size).

Layout, per axis subdirectory:

- `<base>.<engine>.txt`: one engine's transcription of one document.
- `<base>.gold.txt`: NED gold, the reference transcription (rib, hyb).
- `_run*.json`: per-page latency manifest for a GPU-served engine (a list of
  `{"img", "sec", "err", ...}`); the median over `err is None` pages is the
  reported latency.

| Subdir | Documents | Gold | Metric | Committed? |
|---|---|---|---|---|
| `rib` | 200 clean Portuguese pages | `*.gold.txt` | NED | yes (CC BY 4.0) |
| `hyb` | 224 degraded pages (8 types) | `*.gold.txt` | NED + per-degradation | yes (CC BY 4.0) |
| `cost` | classical CPU latency constants | `_classical_latency.json` | latency | yes |
| (root) | IDs paired-bootstrap hits (Surya vs DeepSeek-OCR) | `ids_pair_hits.json` | FVR diff significance | yes (PII-free, integers only) |
| (root) | FORMS paired-bootstrap hits (Qwen2.5-VL vs GLM-OCR) | `forms_pair_hits.json` | FVR diff significance | yes (PII-free, integers only) |
| (root) | IDs paired-bootstrap hits (Surya vs RapidOCR) | `ids_pair_hits_surya_rapidocr.json` | FVR diff significance | yes (PII-free, integers only) |
| (root) | HYB paired-bootstrap NED% (Qwen2.5-VL vs Surya) | `hyb_pair_ned.json` | NED% diff significance | yes (PII-free, floats only) |
| (root) | MinerU IDs FVR hits (single engine) | `ids_mineru_hits.json` | MinerU IDs FVR + Wilson CI | yes (PII-free, integers only) |
| `forms` | 50 Brazilian forms | `*.fields.json` | FVR | no; fetched (XFUND, CC BY-NC-SA) |
| `ids` | 50 Brazilian CNH/RG cards | `*.fields.json` | FVR (date-aware) | no; request (BRIDP) |
| `en` | 30 English forms (VLMs only) | `*.fields.json` | FVR | no; fetched (FUNSD, research-only) |
