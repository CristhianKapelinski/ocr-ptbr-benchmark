# Datasets and the run of record

Five scored sets back the benchmark. For licence and privacy reasons (see
`../data/DATA-LICENSES.md`) the repository commits only the cleanly
redistributable subset and **auto-fetches** the rest from source.

- **Committed (CC BY 4.0, no PII):** the ESTER-Pt RIB/HYB axes under `data/rib`
  and `data/hyb` — per-document reference transcriptions (`*.gold.txt`), the
  per-engine OCR outputs scored against them (`*.<engine>.txt`), and the per-page
  latency manifests (`_run*.json`).
- **Not committed:** the forms (XFUND), identity-document (BRIDP) and
  English-control (FUNSD) raw outputs and gold. Their gold carries
  synthetic-but-realistic PII (names, CPFs, e-mails, addresses, dates of birth)
  under restrictive licences, so they are not redistributed here. Their
  **aggregate scores** are committed as the run of record in
  `../results/run_of_record.json` (numbers only); the no-GPU path regenerates and
  asserts their macros from that file. The from-scratch path fetches their raw
  inputs with `scripts/fetch_data.sh`.
- Document **images** are never committed (licence + size).

| Axis (`data/` dir) | Role | n | Lang | Gold | Source licence | In repo |
|---|---|---|---|---|---|---|
| `forms` | Forms FVR | 50 | PT-BR | image-reconstructed `*.fields.json` | CC BY-NC-SA 4.0 | fetched (XFUND) |
| `ids` | Identity-document FVR | 50 | PT-BR | synthetic structured `*.fields.json` | unstated | request (BRIDP) |
| `en` | English control (VLMs only) | 30 | EN | human-annotated `*.fields.json` | research-only | fetched (FUNSD) |
| `rib` | Clean-text NED | 200 | PT | reference transcription `*.gold.txt` | CC BY 4.0 | committed |
| `hyb` | Degradation-stress NED | 224 | PT | reference transcription `*.gold.txt` | CC BY 4.0 | committed |

- **Forms** are the Portuguese split of a multilingual form-understanding
  benchmark; images are Brazilian administrative templates filled with synthetic
  data and scanned, so they carry no real personal data. The gold is
  reconstructed from the form images (the source key-value gold mixes printed
  instructions and mislinked labels), counting a value only when legibly filled
  into a field. This gold is committed here and is byte-identical (md5) to the run
  used in the paper.
- **Identity documents** are synthetic CNH/RG images whose values are fabricated
  for privacy; the gold is the dataset's own structured fields.
- **English control** is an English benchmark of noisy scanned forms, scored on
  the same FVR scheme on the vision-language models only.
- **RIB / HYB** are the clean and synthetically-degraded partitions of a
  Portuguese text-recognition suite; the degradations are produced by the dataset
  with the DocCreator tool (bleed-through, optical blur, character degradation,
  holes, Gaussian noise, salt-and-pepper noise, phantom ghosting, page rotation).
  Only the license-redistributable gold subsets are released.

## Fetching the sources (from-scratch path only)

`scripts/fetch_data.sh` downloads the not-redistributed sources straight from
their authoritative locations (idempotent, sha256-verified against
`scripts/data.sha256`):

- **XFUND PT split** — `github.com/doc-analysis/XFUND` release v1.0
  (`pt.{train,val}.{json,zip}`), CC BY-NC-SA 4.0.
- **FUNSD** — `guillaumejaume.github.io/FUNSD/dataset.zip`, research-only.
- **ESTER-Pt** — Zenodo record `7872951` (`ESTER-Pt.zip`, ~19.6 GB), CC BY 4.0;
  only the from-scratch path needs the images, the RIB/HYB run of record is
  committed.
- **BRIDP** — no confirmed public download (project page under construction,
  licence unstated); the script prints how to request it from the authors and
  skips it.

To rebuild predictions from scratch, run `scripts/fetch_data.sh`, then run the
engines over the fetched images and hand off to the no-GPU scoring path
(`scripts/run_from_scratch.sh`). The committed run of record makes all of this
unnecessary for reproducing the paper's numbers.
