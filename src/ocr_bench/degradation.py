"""Per-degradation NED breakdown for the degraded HYB axis.

Each HYB page name encodes its DocCreator degradation, e.g.
``page103_Noise_SaltAndPepper_0.png``: strip the leading ``pageNNN_`` and the
trailing ``_<idx>`` to recover the degradation tag. Pages are grouped by tag and
the mean NED% is reported per group, giving the per-degradation matrix in the
paper.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from .config import DEGRADATION_ORDER
from .io import load_ned_pairs
from .scoring import ned_pct

_PAGE_PREFIX = re.compile(r"^page\d+_")
_TRAIL_IDX = re.compile(r"_\d+$")
_PNG_SUFFIX = re.compile(r"\.png$")


def degradation_of(base: str) -> str:
    """Degradation tag from a HYB page base name (without the engine suffix)."""
    tag = _PNG_SUFFIX.sub("", base)
    tag = _PAGE_PREFIX.sub("", tag)
    tag = _TRAIL_IDX.sub("", tag)
    return tag or "unknown"


def per_degradation(hyb_dir: Path, engine: str) -> dict[str, float]:
    """Mean NED% per degradation type for one engine on the HYB axis.

    Returns a mapping in ``DEGRADATION_ORDER`` for the types present; types with
    no scorable page are omitted.
    """
    groups: dict[str, list[float]] = defaultdict(list)
    for doc in load_ned_pairs(hyb_dir, engine):
        v = ned_pct(doc.pred, doc.gold)
        if v is None:
            continue
        groups[degradation_of(doc.base)].append(v)
    return {
        tag: round(sum(vals) / len(vals), 1)
        for tag in DEGRADATION_ORDER
        if (vals := groups.get(tag))
    }
