"""Filesystem access to the committed run of record.

Each axis directory holds, per document, an engine prediction ``<base>.<engine>.txt``
paired with either ``<base>.fields.json`` (FVR gold, a list of ``{key, value}``)
or ``<base>.gold.txt`` (NED gold). Latency manifests are ``_run*.json`` lists of
``{img, sec, err, ...}`` records. Nothing here parses metrics; it only reads bytes.
"""
from __future__ import annotations

import json
import statistics
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FieldGold:
    """One FVR document: its base name and the gold ``{key, value}`` rows."""

    base: str
    rows: list[dict[str, str]]
    pred: str


@dataclass(frozen=True)
class TextGold:
    """One NED document: its base name plus the gold and predicted transcriptions."""

    base: str
    gold: str
    pred: str


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_fvr_pairs(axis_dir: Path, engine: str) -> list[FieldGold]:
    """Yield FVR (gold rows, prediction) pairs for one engine on an axis.

    Only documents that have both a ``*.fields.json`` gold and a matching
    ``*.<engine>.txt`` prediction are returned, so an engine not run on an axis
    yields an empty list rather than crashing.
    """
    out: list[FieldGold] = []
    for gf in sorted(axis_dir.glob("*.fields.json")):
        base = gf.name[: -len(".fields.json")]
        pf = axis_dir / f"{base}.{engine}.txt"
        if not pf.exists():
            continue
        rows = json.loads(_read(gf))
        out.append(FieldGold(base=base, rows=rows, pred=_read(pf)))
    return out


def load_ned_pairs(axis_dir: Path, engine: str) -> list[TextGold]:
    """Yield NED (gold, prediction) pairs for one engine on an axis."""
    suffix = f".{engine}.txt"
    out: list[TextGold] = []
    for pf in sorted(axis_dir.glob(f"*{suffix}")):
        base = pf.name[: -len(suffix)]
        gf = axis_dir / f"{base}.gold.txt"
        if not gf.exists():
            continue
        out.append(TextGold(base=base, gold=_read(gf), pred=_read(pf)))
    return out


def load_latency_median(manifest: Path) -> float | None:
    """Median seconds/page over the successful (``err is None``) pages of a manifest."""
    if not manifest.exists():
        return None
    recs = json.loads(_read(manifest))
    secs = [r["sec"] for r in recs
            if r.get("err") is None and isinstance(r.get("sec"), (int, float))]
    if not secs:
        return None
    return round(statistics.median(secs), 2)
