# Datasets and the run of record

Five scored sets back the benchmark. The committed run of record under `data/`
holds, per document, the per-engine OCR transcriptions (`*.<engine>.txt`), the
gold answer set (`*.fields.json` for FVR, `*.gold.txt` for NED), and the per-page
latency manifests (`_run*.json`). The document **images** are not redistributed
(license and size); only the from-scratch generation path needs them.

| Axis (`data/` dir) | Role | n | Lang | Gold | Source license |
|---|---|---|---|---|---|
| `forms` | Forms FVR | 50 | PT-BR | image-reconstructed `*.fields.json` | CC BY-NC-SA 4.0 |
| `ids` | Identity-document FVR | 50 | PT-BR | synthetic structured `*.fields.json` | unstated (synthetic) |
| `en` | English control (VLMs only) | 30 | EN | human-annotated `*.fields.json` | research-only |
| `rib` | Clean-text NED | 200 | PT | reference transcription `*.gold.txt` | CC BY 4.0 |
| `hyb` | Degradation-stress NED | 224 | PT | reference transcription `*.gold.txt` | CC BY 4.0 |

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

To rebuild predictions from scratch, place the source images alongside their gold
under `$WORK_DIR/<axis>/` and run `scripts/run_from_scratch.sh`. The committed
run of record makes this unnecessary for reproducing the paper's numbers.
