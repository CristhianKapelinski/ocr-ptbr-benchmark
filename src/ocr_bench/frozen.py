"""The committed run of record for the not-redistributed axes.

The forms (XFUND), identity-document (BRIDP) and English-control (FUNSD) raw
per-engine transcriptions and gold are **not** redistributed in this repository
for licence and privacy reasons (see ``data/DATA-LICENSES.md``): their gold
carries synthetic-but-realistic PII (names, CPFs, e-mails, addresses, dates of
birth) under restrictive licences. What *is* committed is their aggregate run of
record -- the per-engine scores already computed from those outputs -- in
``results/consolidated_results.json``.

This module loads those aggregate score blocks so the no-GPU reproduce path can
regenerate and assert the forms/ids/en macros without ever touching raw field
values. The clean ESTER-Pt RIB/HYB axis (CC BY 4.0, public-domain literature, no
PII) is re-scored live from its committed outputs and never read from here.

The source is ``results/run_of_record.json``, an immutable committed file that
holds the aggregate scores only. It is deliberately separate from the
regenerated ``results/consolidated_results.json`` that ``ocr-bench reproduce``
writes, so re-running the reproduce path never clobbers the run of record.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# The restricted axes whose raw outputs are not redistributed; their scores are
# taken from the committed run of record instead of being re-derived from data.
RESTRICTED_AXES = ("forms", "ids", "en")

_RECORD = (
    Path(__file__).resolve().parents[2] / "results" / "run_of_record.json"
)


def _load(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"committed run of record not found at {path}; it holds the aggregate "
            "scores for the not-redistributed forms/ids/en axes and is required "
            "by the no-GPU reproduce path"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def restricted_block(engine: str, record: Path = _RECORD) -> dict[str, Any]:
    """Aggregate forms/ids/en/latency blocks for one engine, from the run of record.

    Returns only the not-redistributed fields: the ``forms``, ``ids`` and ``en``
    score blocks and the ``latency`` block (whose forms/ids medians come from the
    restricted axes). RIB and HYB are intentionally excluded so they are always
    re-scored live from the committed ESTER-Pt outputs.
    """
    blocks = _load(record)
    block = blocks.get(engine, {})
    return {
        "forms": block.get("forms"),
        "ids": block.get("ids"),
        "en": block.get("en"),
        "latency": block.get("latency", {}),
    }
