"""MinerU IDs field-value recall from a committed PII-free hit array.

The identity-document axis is not redistributed and its gold carries
synthetic PII, so MinerU's IDs FVR cannot be re-derived from raw field values on
the reviewer's clone. What *is* committed is ``data/ids_mineru_hits.json``: for
every scored IDs gold field, a single ``[doc_index, hit]`` row where ``hit`` is
0/1, plus integer metadata (recovered/total counts, empty-document tally, seed).
No field value, transcription, gold text or document name is present -- only
integers and the schema keys -- exactly like the existing paired-bootstrap hit
files (:mod:`ocr_bench.bootstrap`).

The original date-aware substring match (the same rule as every other engine's
IDs FVR: a gold value is recovered iff any of its normalized printed-date
variants is a substring of the normalized transcription, dropping length-<=1 gold
values) was applied once on the GPU host to produce these hits. Here we only sum
them back into the micro-averaged FVR and its analytic 95% Wilson interval, so
``\\idsMineru`` and its CI reproduce offline without ever touching identity data.
The 19 ID cards that returned empty MinerU output contribute their fields as
genuine zeros (they are already 0 in the committed array).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .scoring import wilson_ci

# The committed PII-free run of record for MinerU's IDs (date-aware) FVR.
HITS_FILE = Path(__file__).resolve().parents[2] / "data" / "ids_mineru_hits.json"


def load_hits(path: Path = HITS_FILE) -> tuple[list[int], dict[str, Any]]:
    """Load the committed 0/1 hit array and the file's integer metadata block."""
    meta = json.loads(path.read_text(encoding="utf-8"))
    hits = [hit for _doc, hit in meta["pairs"]]
    return hits, meta


def score_ids(path: Path = HITS_FILE) -> dict[str, Any] | None:
    """Micro FVR with a Wilson CI for MinerU on IDs, from the committed hits.

    Mirrors :func:`ocr_bench.aggregate.score_fvr` field for field (same Wilson
    interval, same 3-dp rounding); the per-field hits were produced once with the
    identical date-aware substring rule, so the result is byte-faithful to a live
    re-score of the identity axis.
    """
    hits, meta = load_hits(path)
    tot = len(hits)
    if tot == 0:
        return None
    rec = sum(hits)
    lo, hi = wilson_ci(rec, tot)
    return {
        "fvr": round(rec / tot, 3),
        "ci": [round(lo, 3), round(hi, 3)],
        "recovered": rec,
        "total": tot,
        # The ID cards that returned empty MinerU output (scored as genuine zeros);
        # surfaced for the \minerEmptyIDs macro.
        "empty_docs": meta.get("empty_docs"),
    }
