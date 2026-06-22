# Run of record

This directory holds the committed run of record the no-GPU reproduce path scores
offline. For licence and privacy reasons only the cleanly redistributable subset
is committed here (see `DATA-LICENSES.md`):

- **`rib/`, `hyb/`** — the ESTER-Pt clean and degraded axes (CC BY 4.0,
  public-domain literature, no PII): per-document `*.gold.txt` reference
  transcriptions and the per-engine `*.<engine>.txt` outputs scored against them,
  plus `_run*.json` per-page latency manifests for the GPU-served engines.
- **`cost/_classical_latency.json`** — measured CPU latency medians for the
  classical pipelines (aggregate numbers, no document content).

The **forms (XFUND), identity-document (BRIDP) and English-control (FUNSD)** raw
outputs and gold are **not** committed: their gold carries synthetic PII (names,
CPFs, e-mails, addresses, dates of birth) under restrictive licences. Their
**aggregate scores** are the run of record in `../results/run_of_record.json`
(numbers only), which the reproduce path uses to regenerate and assert their
macros. To rebuild them from scratch, `scripts/fetch_data.sh` downloads the source
inputs (XFUND PT, FUNSD; BRIDP must be requested from its authors). Document
images are never committed (licence + size).

Layout, per axis subdirectory:

- `<base>.<engine>.txt` — one engine's transcription of one document.
- `<base>.gold.txt` — NED gold: the reference transcription (rib, hyb).
- `_run*.json` — per-page latency manifest for a GPU-served engine (a list of
  `{"img", "sec", "err", ...}`); the median over `err is None` pages is the
  reported latency.

| Subdir | Documents | Gold | Metric | Committed? |
|---|---|---|---|---|
| `rib` | 200 clean Portuguese pages | `*.gold.txt` | NED | yes (CC BY 4.0) |
| `hyb` | 224 degraded pages (8 types) | `*.gold.txt` | NED + per-degradation | yes (CC BY 4.0) |
| `cost` | classical CPU latency constants | `_classical_latency.json` | latency | yes |
| `forms` | 50 Brazilian forms | `*.fields.json` | FVR | no — fetched (XFUND, CC BY-NC-SA) |
| `ids` | 50 Brazilian CNH/RG cards | `*.fields.json` | FVR (date-aware) | no — request (BRIDP) |
| `en` | 30 English forms (VLMs only) | `*.fields.json` | FVR | no — fetched (FUNSD, research-only) |
