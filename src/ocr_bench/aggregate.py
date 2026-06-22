"""Score every engine on every axis and assemble the consolidated results.

This is the analysis core of the no-GPU reproduce path. It walks the committed
run of record, applies the FVR / NED scorers, recomputes per-page latency
medians, and emits one nested dict mirroring the paper's results structure. The
LaTeX-macro and figure layers consume this dict; nothing here writes files.
"""
from __future__ import annotations

from typing import Any

from . import latency
from .config import (
    AXIS_BY_KEY,
    EN_SCORED,
    ENGINES,
    FORMS_ONLY,
    HYB_NO_BREAKDOWN,
    data_root,
)
from .degradation import per_degradation
from .io import load_fvr_pairs, load_ned_pairs
from .scoring import (
    alnum_norm,
    bootstrap_ci,
    date_candidates,
    ned_pct,
    wilson_ci,
)

# A normalized prediction shorter than this is a degenerate (near-empty) output;
# the excl-degenerate forms FVR drops those forms and is reported alongside raw.
DEGEN_MIN_CHARS = 20


def _round(x: float | None, n: int) -> float | None:
    return None if x is None else round(x, n)


def score_fvr(axis_key: str, engine: str, date_aware: bool,
              drop_short: bool) -> dict[str, Any] | None:
    """Micro FVR with a Wilson CI over the gold field values of one axis."""
    pairs = load_fvr_pairs(data_root() / AXIS_BY_KEY[axis_key].subdir, engine)
    if not pairs:
        return None
    rec = tot = 0
    for doc in pairs:
        pred = alnum_norm(doc.pred)
        for row in doc.rows:
            value = row.get("value", "")
            cands = date_candidates(value) if date_aware else {alnum_norm(value)}
            cands = {c for c in cands if c}
            if not cands or (drop_short and len(alnum_norm(value)) <= 1):
                continue
            tot += 1
            rec += any(c in pred for c in cands)
    if tot == 0:
        return None
    lo, hi = wilson_ci(rec, tot)
    return {"fvr": round(rec / tot, 3), "ci": [_round(lo, 3), _round(hi, 3)],
            "recovered": rec, "total": tot}


def score_forms(engine: str) -> dict[str, Any] | None:
    """Forms FVR with the excl-degenerate variant (drops forms with <20-char preds)."""
    pairs = load_fvr_pairs(data_root() / "forms", engine)
    if not pairs:
        return None
    rec = tot = 0
    rec_x = tot_x = degen = 0
    for doc in pairs:
        pred = alnum_norm(doc.pred)
        short = len(pred) < DEGEN_MIN_CHARS
        if short:
            degen += 1
        for row in doc.rows:
            nv = alnum_norm(row.get("value", ""))
            if not nv:
                continue
            tot += 1
            hit = nv in pred
            rec += hit
            if not short:
                tot_x += 1
                rec_x += hit
    lo, hi = wilson_ci(rec, tot)
    return {
        "fvr": round(rec / tot, 3),
        "ci": [_round(lo, 3), _round(hi, 3)],
        "fvr_excl_degen": round(rec_x / tot_x, 3) if tot_x else round(rec / tot, 3),
        "degen_n": degen,
    }


def score_ned(axis_key: str, engine: str) -> dict[str, Any] | None:
    """Mean NED% with a seeded bootstrap CI over per-document values."""
    pairs = load_ned_pairs(data_root() / AXIS_BY_KEY[axis_key].subdir, engine)
    vals = [v for doc in pairs if (v := ned_pct(doc.pred, doc.gold)) is not None]
    if not vals:
        return None
    lo, hi = bootstrap_ci(vals)
    empty = sum(1 for doc in pairs if not doc.pred.strip())
    return {"ned": round(sum(vals) / len(vals), 2),
            "ci": [_round(lo, 2), _round(hi, 2)], "n": len(vals), "empty": empty}


def score_engine(engine: str, etype: str) -> dict[str, Any]:
    """Full per-axis result block for one engine."""
    forms = score_forms(engine)
    ids = (None if engine in FORMS_ONLY
           else score_fvr("ids", engine, date_aware=True, drop_short=True))
    en = (score_fvr("en", engine, date_aware=False, drop_short=False)
          if engine in EN_SCORED else None)
    rib = None if engine in FORMS_ONLY else score_ned("rib", engine)
    hyb_block = None
    if engine not in FORMS_ONLY:
        hyb = score_ned("hyb", engine)
        if hyb is not None:
            hyb_block = dict(hyb)
            if engine not in HYB_NO_BREAKDOWN:
                bd = per_degradation(data_root() / "hyb", engine)
                if bd:
                    hyb_block["by_degradation"] = bd

    lat: dict[str, float | None] = {}
    if etype == "classical":
        cls = latency.classical_latency().get(engine, {})
        lat = {"forms_med": cls.get("forms"), "ids_med": cls.get("ids"),
               "rib_med": None, "hyb_med": None}
    else:
        lat = {
            "forms_med": latency.gpu_latency("forms", engine),
            "ids_med": None if engine in FORMS_ONLY else latency.gpu_latency("ids", engine),
            "rib_med": None if engine in FORMS_ONLY else latency.gpu_latency("rib", engine),
            "hyb_med": None if engine in FORMS_ONLY else latency.gpu_latency("hyb", engine),
        }

    return {"forms": forms, "ids": ids, "en": en, "rib": rib,
            "hyb": hyb_block, "latency": lat}


def consolidate() -> dict[str, Any]:
    """Score the whole roster; returns ``{engine_key: result_block}``."""
    return {e.key: {"display": e.display, "type": e.type, "params": e.params,
                    **score_engine(e.key, e.type)}
            for e in ENGINES}
