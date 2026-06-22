# Run of record

This directory is the committed run of record: the per-engine OCR outputs and
gold the no-GPU reproduce path scores offline. It is the one deliberate
exception to `.gitignore`'s "no regenerable blobs" rule. Document images are not
committed (license + size); see `../docs/DATASETS.md`.

Layout, per axis subdirectory:

- `<base>.<engine>.txt` — one engine's transcription of one document.
- `<base>.fields.json` — FVR gold: a list of `{"key", "value"}` (forms, ids, en).
- `<base>.gold.txt` — NED gold: the reference transcription (rib, hyb).
- `_run*.json` — per-page latency manifest for a GPU-served engine (a list of
  `{"img", "sec", "err", ...}`); the median over `err is None` pages is the
  reported latency.

| Subdir | Documents | Gold | Metric |
|---|---|---|---|
| `forms` | 50 Brazilian forms | `*.fields.json` | FVR |
| `ids` | 50 Brazilian CNH/RG cards | `*.fields.json` | FVR (date-aware) |
| `en` | 30 English forms (VLMs only) | `*.fields.json` | FVR |
| `rib` | 200 clean Portuguese pages | `*.gold.txt` | NED |
| `hyb` | 224 degraded pages (8 types) | `*.gold.txt` | NED + per-degradation |
| `cost` | classical CPU latency constants | `_classical_latency.json` | latency |
