# Data licences and redistribution policy

This repository's **code** is MIT (see `../LICENSE`). The **data** is governed by
the source datasets' own licences, and only the cleanly redistributable subset is
committed here. The rest is auto-fetched from source by `scripts/fetch_data.sh`.

## What IS redistributed in this repository

| Path | Content | Source | Licence |
|---|---|---|---|
| `data/rib/`, `data/hyb/` | ESTER-Pt clean (RIB) and degraded (HYB) reference transcriptions (`*.gold.txt`) and the per-engine OCR outputs scored against them | ESTER-Pt (Zenodo `7872951`) | **CC BY 4.0** |
| `data/cost/_classical_latency.json` | Aggregate CPU latency medians (no document content) | this work | MIT |
| `data/*_pair_*.json`, `data/ids_mineru_hits.json` | PII-free derived significance inputs: per-field `0/1` hit arrays and per-page NED% floats plus integer document indices (no field text, transcription or gold) | this work | MIT |
| `results/run_of_record.json`, `results/consolidated_results.json` | Aggregate per-engine scores for **all** axes (numbers only, no raw field values) | this work | MIT |

ESTER-Pt is public-domain Portuguese literature with **no personal data**, so its
gold and the transcriptions are redistributed here under CC BY 4.0. **Attribution:**
ESTER-Pt: An Evaluation Suite for TExt Recognition in Portuguese, Zenodo,
https://doi.org/10.5281/zenodo.7872951 (CC BY 4.0).

## What is NOT redistributed (fetched from source instead)

The forms, identity-document and English-control raw inputs are **not** committed:
their gold carries synthetic-but-realistic PII (names, CPFs, e-mails, addresses,
dates of birth) and their licences forbid or do not permit redistribution here.
Their **aggregate scores** are committed (in `results/`) as the run of record, and
`scripts/fetch_data.sh` downloads the raw inputs from source for the from-scratch
path under each source's own licence:

| Axis | Dataset | Source | Licence | Auto-fetch |
|---|---|---|---|---|
| forms | XFUND (PT split) | github.com/doc-analysis/XFUND release v1.0 | **CC BY-NC-SA 4.0** | yes |
| en | FUNSD | guillaumejaume.github.io/FUNSD | **research-only** | yes |
| ids | BRIDP | lucassfer.github.io/bridp | **unstated** (page under construction) | no -- request from authors |

Because these are fetched under their own licences and not redistributed here,
this repository imposes no additional restriction on them; the user is bound by
each source dataset's licence when fetching it. BRIDP has no confirmed public
download, so `fetch_data.sh` prints how to request it and skips it.

## Privacy

No raw PII-bearing field value is committed anywhere in this repository. The
committed tree contains only public-domain literary text (ESTER-Pt) and aggregate
numbers (latency medians, per-engine scores, and the PII-free `0/1` hit / NED%
arrays that drive the significance tests and MinerU's IDs FVR). The no-GPU
reproduce path reads only these and never touches forms/ids/en raw field values.
MinerU's RIB/HYB outputs are the ESTER-Pt CC BY 4.0 transcriptions (the same
public-domain literature already redistributed), not BRIDP.
