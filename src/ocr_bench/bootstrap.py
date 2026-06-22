"""Paired document-level bootstrap significance test on the IDs axis.

The headline IDs claim is that the specialized engine (Surya) beats the best
vision-language model (DeepSeek-OCR) by a margin whose 95% confidence interval
excludes zero. Establishing that requires a *paired* test that respects the
clustering of fields within documents, so this module reproduces the
significance result from a PII-free run of record without ever touching the raw
BRIDP field values.

The committed input is ``data/ids_pair_hits.json``: for every scored IDs gold
field it stores the pair ``[surya_hit, deepseek_hit]`` (each 0/1) tagged with an
integer document index. No field value, transcription, gold text or document
name is present -- only integers and the schema keys. The original per-field
match logic (date-aware substring recall, dropping length-<=1 gold values) was
applied once, on the GPU host, to produce those hits; here we only resample them.

The procedure mirrors the from-scratch harness exactly: resample the documents
with replacement ``B`` times (clustered / document-level bootstrap), recompute
the micro-averaged FVR of each engine on each resample, and take the percentile
CI of the per-resample difference (engine A minus engine B). The point estimate
is the observed difference; the marginals are the observed micro FVRs. Stdlib
only and fully deterministic given the seed, so the CI bounds are exact.
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import BOOT_N, BOOT_SEED

# The committed PII-free run of record for the paired IDs test.
HITS_FILE = (
    Path(__file__).resolve().parents[2] / "data" / "ids_pair_hits.json"
)


@dataclass(frozen=True)
class DocHits:
    """One document's per-field hit vectors for the two compared engines."""

    hits_a: list[int]
    hits_b: list[int]


def load_doc_hits(path: Path = HITS_FILE) -> tuple[list[DocHits], dict[str, Any]]:
    """Load the committed hit array, grouped into per-document clusters.

    Returns the per-document hit vectors (the resampling unit) and the file's
    metadata block (engine names, expected counts, seed/B) so callers can both
    resample and assert against the recorded run of record.
    """
    meta = json.loads(path.read_text(encoding="utf-8"))
    pairs = meta["pairs"]  # list of [doc_index, hit_a, hit_b]
    by_doc: dict[int, DocHits] = {}
    for doc, ha, hb in pairs:
        bucket = by_doc.setdefault(doc, DocHits([], []))
        bucket.hits_a.append(ha)
        bucket.hits_b.append(hb)
    docs = [by_doc[i] for i in sorted(by_doc)]
    return docs, meta


def _micro_fvr(docs: list[DocHits]) -> tuple[float, float]:
    """Micro-averaged FVR for each engine over a (possibly multiset) doc list."""
    ra = ta = rb = tb = 0
    for d in docs:
        ra += sum(d.hits_a)
        ta += len(d.hits_a)
        rb += sum(d.hits_b)
        tb += len(d.hits_b)
    fa = ra / ta if ta else 0.0
    fb = rb / tb if tb else 0.0
    return fa, fb


def _percentile(sorted_vals: list[float], q: float) -> float:
    """Linear-interpolated percentile over a sorted list (NIST/numpy 'linear')."""
    if not sorted_vals:
        return 0.0
    idx = q * (len(sorted_vals) - 1)
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return sorted_vals[lo]
    frac = idx - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


@dataclass(frozen=True)
class PairBootstrap:
    """Result of the paired document-level bootstrap difference test."""

    fvr_a: float
    fvr_b: float
    diff: float
    ci_lo: float
    ci_hi: float
    excludes_zero: bool
    n_docs: int
    n_fields: int
    b: int
    seed: int


def paired_bootstrap(
    docs: list[DocHits] | None = None,
    b: int = BOOT_N,
    seed: int = BOOT_SEED,
) -> PairBootstrap:
    """Run the clustered paired bootstrap of the IDs FVR difference (A minus B).

    Resamples the documents with replacement ``b`` times, recomputes each
    engine's micro FVR per resample, and returns the observed marginals, the
    observed difference, and the 95% percentile CI of the resampled difference.
    Deterministic given ``seed``.
    """
    if docs is None:
        docs, _ = load_doc_hits()
    n_docs = len(docs)
    n_fields = sum(len(d.hits_a) for d in docs)

    fa, fb = _micro_fvr(docs)
    diff_point = fa - fb

    rng = random.Random(seed)
    diffs: list[float] = []
    for _ in range(b):
        sample = [docs[rng.randrange(n_docs)] for _ in range(n_docs)]
        sfa, sfb = _micro_fvr(sample)
        diffs.append(sfa - sfb)
    diffs.sort()
    ci_lo = _percentile(diffs, 0.025)
    ci_hi = _percentile(diffs, 0.975)

    return PairBootstrap(
        fvr_a=fa,
        fvr_b=fb,
        diff=diff_point,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        excludes_zero=(ci_lo > 0.0) or (ci_hi < 0.0),
        n_docs=n_docs,
        n_fields=n_fields,
        b=b,
        seed=seed,
    )


def build_pair_macros(result: PairBootstrap) -> dict[str, str]:
    """Map the paired-bootstrap macro names to their 3-dp rendered values.

    These are the macros the paper compiles for the IDs significance test:
    ``\\idsPairDiff`` (point lead), ``\\idsPairLo`` / ``\\idsPairHi`` (95% CI),
    and the two marginal FVRs ``\\idsPairSurya`` / ``\\idsPairDeepSeek``. The
    point lead is the difference of the *printed* (3-dp) marginals, matching the
    paper's table (0.921 - 0.864 = 0.057); the raw difference 0.0565 prints to
    the same value once the marginals are the displayed quantities.
    """
    surya = round(result.fvr_a, 3)
    deepseek = round(result.fvr_b, 3)
    return {
        "idsPairSurya": repr(surya),
        "idsPairDeepSeek": repr(deepseek),
        "idsPairDiff": repr(round(surya - deepseek, 3)),
        "idsPairLo": repr(round(result.ci_lo, 3)),
        "idsPairHi": repr(round(result.ci_hi, 3)),
    }


def summary(result: PairBootstrap, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """A JSON-serializable summary block for the consolidated results."""
    a = (meta or {}).get("engine_a", "surya")
    b = (meta or {}).get("engine_b", "deepseekocr")
    return {
        "engine_a": a,
        "engine_b": b,
        "n_docs": result.n_docs,
        "n_fields": result.n_fields,
        "fvr_a": round(result.fvr_a, 4),
        "fvr_b": round(result.fvr_b, 4),
        "diff_point": round(result.diff, 4),
        "B": result.b,
        "seed": result.seed,
        "ci95_diff": [round(result.ci_lo, 4), round(result.ci_hi, 4)],
        "ci_excludes_zero": result.excludes_zero,
    }
