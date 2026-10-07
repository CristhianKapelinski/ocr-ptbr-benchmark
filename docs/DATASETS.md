# Datasets and the run of record

Five scored sets back the benchmark. For license and privacy reasons (see
`../data/DATA-LICENSES.md`) the repository commits only the cleanly
redistributable subset and **auto-fetches** the rest from source.

- **Committed (CC BY 4.0, no PII):** the ESTER-Pt RIB/HYB axes under `data/rib`
  and `data/hyb`: per-document reference transcriptions (`*.gold.txt`), the
  per-engine OCR outputs scored against them (`*.<engine>.txt`), and the per-page
  latency manifests (`_run*.json`).
- **Not committed:** the forms (XFUND), identity-document and
  English-control (FUNSD) raw outputs and gold. Their gold carries
  synthetic-but-realistic PII (names, CPFs, e-mails, addresses, dates of birth)
  under restrictive licences, so they are not redistributed here. Their
  **aggregate scores** are committed as the run of record in
  `../results/run_of_record.json` (numbers only); the no-GPU path regenerates and
  asserts their macros from that file. The from-scratch path fetches their raw
  inputs with `scripts/fetch_data.sh`.
- **Committed, PII-free derived inputs:** four paired-bootstrap arrays drive the
  significance tests in the no-GPU path. The FVR arrays: `ids_pair_hits.json`
  (Surya vs DeepSeek-OCR), `forms_pair_hits.json` (Qwen2.5-VL vs GLM-OCR) and
  `ids_pair_hits_surya_rapidocr.json` (Surya vs RapidOCR): store, for every scored
  field, the binary hit pair `[a_hit, b_hit]` (`0/1`) plus an integer document index.
  The NED array `hyb_pair_ned.json` (Qwen2.5-VL vs Surya) stores, per HYB page, the
  `[a_ned, b_ned]` NED% floats plus an integer index. All four are derived once from
  the raw outputs on the GPU host and contain no field value, transcription or gold
  text; only integers/floats.
- Document **images** are never committed (license + size).

| Axis (`data/` dir) | Role | n | Lang | Gold | Source license | In repo |
|---|---|---|---|---|---|---|
| `forms` | Forms FVR | 50 | PT-BR | image-reconstructed `*.fields.json` | CC BY-NC-SA 4.0 | fetched (XFUND) |
| `ids` | Identity-document FVR | 50 | PT-BR | synthetic structured `*.fields.json` (LLM-drafted, manually reviewed by the dataset authors) | unstated | fetched (tech4humans/br-doc-extraction) |
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

- **XFUND PT split**: `github.com/doc-analysis/XFUND` release v1.0
  (`pt.{train,val}.{json,zip}`), CC BY-NC-SA 4.0.
- **FUNSD**: `guillaumejaume.github.io/FUNSD/dataset.zip`, research-only.
- **ESTER-Pt**: Zenodo record `7872951` (`ESTER-Pt.zip`, ~19.6 GB), CC BY 4.0;
  only the from-scratch path needs the images, the RIB/HYB run of record is
  committed.
- **Identity documents**: the 25 CNH + 25 RG rows of the `valid` split of
  tech4humans/br-doc-extraction (Hugging Face), whose images were sampled from the
  BID Dataset; the split's 25 invoice rows are skipped. `scripts/ids_from_parquet.py`
  writes them in the scorer's format, and the result yields the paper's 354 scored
  fields. See the Erratum in `../README.md`.

To rebuild predictions from scratch, run `scripts/fetch_data.sh`, then run the
engines over the fetched images and hand off to the no-GPU scoring path
(`scripts/run_from_scratch.sh`). The committed run of record makes all of this
unnecessary for reproducing the paper's numbers.
