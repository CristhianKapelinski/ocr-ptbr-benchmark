"""Core metrics: field-value recall (FVR) and normalized edit distance (NED).

Both metrics are pure-stdlib so the no-GPU scoring path runs with no third-party
dependency. The implementations are byte-faithful to the original harness
scorers (``score_fvr50_axis_final.py`` and ``score_ned_tesseract.py``):

- FVR: a gold field value counts as recovered iff its alphanumeric-normalized
  form (or, for ISO dates, any printed-format variant) is a substring of the
  alphanumeric-normalized transcription. Reported as the micro proportion with a
  95% Wilson interval. Free-credit gold values of length <= 1 are dropped.
- NED: ``1 - min(lev(norm(pred), norm(gold)) / max(len(norm(gold)), 1), 1)``,
  expressed in percent, with NFC / lower / whitespace-collapse normalization and
  a deterministic seeded bootstrap CI over per-document values.
"""
from __future__ import annotations

import math
import random
import re
import statistics
import unicodedata
from collections.abc import Sequence

from .config import BOOT_N, BOOT_SEED, WILSON_Z

_ALNUM = re.compile(r"[^a-z0-9]")
_WS = re.compile(r"\s+")
_ISO_DATE = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})\s*$")


def alnum_norm(s: str | None) -> str:
    """Lowercase and strip every non-alphanumeric character (FVR normalization)."""
    return _ALNUM.sub("", (s or "").lower())


def text_norm(s: str) -> str:
    """NFC + lowercase + collapse-whitespace normalization (NED normalization)."""
    return _WS.sub(" ", unicodedata.normalize("NFC", s).lower()).strip()


def _levenshtein_py(a: str, b: str) -> int:
    """Reference pure-stdlib Levenshtein, O(len(a)*len(b)) time, O(len(b)) space.

    Kept as a dependency-free fallback so the scorer runs even without rapidfuzz;
    rapidfuzz's C implementation returns the identical integer distance.
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


try:
    from rapidfuzz.distance import Levenshtein as _RFL

    def levenshtein(a: str, b: str) -> int:
        """Levenshtein edit distance (rapidfuzz C backend; identical to the
        reference implementation, used for speed on long literary pages)."""
        return _RFL.distance(a, b)
except ImportError:  # pragma: no cover - exercised only without the wheel
    levenshtein = _levenshtein_py


def ned(pred: str, gold: str) -> float | None:
    """Normalized edit distance in [0, 1]; ``None`` when gold is empty."""
    g = text_norm(gold)
    if not g:
        return None
    p = text_norm(pred)
    return min(levenshtein(p, g) / max(len(g), 1), 1.0)


def ned_pct(pred: str, gold: str) -> float | None:
    """NED similarity in percent; ``None`` when gold is empty."""
    d = ned(pred, gold)
    return None if d is None else (1.0 - d) * 100.0


def date_candidates(value: str | None) -> set[str]:
    """Normalized match candidates for a gold value, expanding ISO dates.

    BRIDP gold stores dates as ``YYYY-MM-DD`` while the cards print
    ``DD/MM/YYYY``; without this expansion the plain substring rule could never
    match a printed date.
    """
    v = (value or "").strip()
    out = {alnum_norm(v)}
    m = _ISO_DATE.match(v)
    if m:
        y, mo, d = m.groups()
        out.add(alnum_norm(d + mo + y))
        out.add(alnum_norm(d + "/" + mo + "/" + y))
        out.add(alnum_norm(str(int(d)) + str(int(mo)) + y))
    return {x for x in out if x}


def wilson_ci(k: int, n: int, z: float = WILSON_Z) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion ``k/n``."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((centre - half) / denom, (centre + half) / denom)


def bootstrap_ci(
    vals: Sequence[float],
    n: int = BOOT_N,
    seed: int = BOOT_SEED,
) -> tuple[float | None, float | None]:
    """Deterministic 95% percentile bootstrap CI over per-document values."""
    if len(vals) < 2:
        return (None, None)
    rng = random.Random(seed)
    k = len(vals)
    reps = []
    for _ in range(n):
        sample = [vals[rng.randrange(k)] for _ in range(k)]
        reps.append(statistics.mean(sample))
    reps.sort()
    return (reps[int(0.025 * n)], reps[int(0.975 * n)])
