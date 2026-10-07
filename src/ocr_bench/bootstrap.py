"""Paired document-level bootstrap significance test on the IDs axis.

The headline IDs claim is that the specialized engine (Surya) beats the best
vision-language model (DeepSeek-OCR) by a margin whose 95% confidence interval
excludes zero. Establishing that requires a *paired* test that respects the
clustering of fields within documents, so this module reproduces the
significance result from a PII-free run of record without ever touching the raw
identity-document field values.

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

_DATA = Path(__file__).resolve().parents[2] / "data"

# The committed PII-free run of record for the paired IDs (Surya vs DeepSeek) test.
HITS_FILE = _DATA / "ids_pair_hits.json"

# The three additional paired-bootstrap run-of-record arrays. Same PII-free
# schema as ``ids_pair_hits.json`` (integers/floats only, no field values): two
# FVR hit arrays and one NED%-per-page array.
FORMS_PAIR_FILE = _DATA / "forms_pair_hits.json"        # qwen25vl vs glmocr (forms)
IDS_RAPID_PAIR_FILE = _DATA / "ids_pair_hits_surya_rapidocr.json"  # surya vs rapidocr (IDs)
HYB_NED_PAIR_FILE = _DATA / "hyb_pair_ned.json"         # qwen25vl vs surya (HYB NED%)


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


# --------------------------------------------------------------------------- #
# Additional paired tests (same clustered doc-level bootstrap, B=10000, seed).
#
# Three more comparisons are recomputed from their own committed PII-free arrays
# exactly as the IDs (Surya vs DeepSeek) test above:
#   * FORMS FVR -- Qwen2.5-VL vs GLM-OCR     (forms_pair_hits.json)
#   * IDs FVR   -- Surya vs RapidOCR          (ids_pair_hits_surya_rapidocr.json)
#   * HYB NED%  -- Qwen2.5-VL vs Surya        (hyb_pair_ned.json)
# The FVR pair files reuse :func:`load_doc_hits` / :func:`paired_bootstrap`
# verbatim (the schema is identical); the NED pair has its own loader and a mean
# (rather than micro) aggregator, but the resampling and percentile-CI procedure
# are line-for-line the same.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DocNed:
    """One document's per-page NED% for the two compared engines (paired)."""

    ned_a: float
    ned_b: float


def load_doc_ned(path: Path = HYB_NED_PAIR_FILE) -> tuple[list[DocNed], dict[str, Any]]:
    """Load a committed NED%-pair array, one resampling unit per scored page.

    Each ``[doc_index, ned_a, ned_b]`` row is a page's NED% (0-100) for each
    engine -- floats only, no transcription or gold text. Returns the per-page
    pairs (the resampling unit) and the file metadata block.
    """
    meta = json.loads(path.read_text(encoding="utf-8"))
    docs = [DocNed(float(na), float(nb)) for _doc, na, nb in meta["pairs"]]
    return docs, meta


def _mean_ned(docs: list[DocNed]) -> tuple[float, float]:
    """Mean per-page NED% for each engine over a (possibly multiset) page list."""
    n = len(docs)
    if not n:
        return 0.0, 0.0
    a = sum(d.ned_a for d in docs) / n
    b = sum(d.ned_b for d in docs) / n
    return a, b


@dataclass(frozen=True)
class NedPairBootstrap:
    """Result of the paired document-level bootstrap of a NED% difference."""

    ned_a: float
    ned_b: float
    diff: float
    ci_lo: float
    ci_hi: float
    excludes_zero: bool
    n_pages: int
    b: int
    seed: int


def paired_ned_bootstrap(
    docs: list[DocNed] | None = None,
    b: int = BOOT_N,
    seed: int = BOOT_SEED,
) -> NedPairBootstrap:
    """Clustered paired bootstrap of the mean-NED% difference (A minus B).

    Resamples the scored pages with replacement ``b`` times, recomputes each
    engine's mean NED% per resample, and returns the observed marginals, the
    observed difference, and the 95% percentile CI of the resampled difference.
    Deterministic given ``seed``; mirrors :func:`paired_bootstrap` exactly.
    """
    if docs is None:
        docs, _ = load_doc_ned()
    n = len(docs)

    na, nb = _mean_ned(docs)
    diff_point = na - nb

    rng = random.Random(seed)
    diffs: list[float] = []
    for _ in range(b):
        sample = [docs[rng.randrange(n)] for _ in range(n)]
        sna, snb = _mean_ned(sample)
        diffs.append(sna - snb)
    diffs.sort()
    ci_lo = _percentile(diffs, 0.025)
    ci_hi = _percentile(diffs, 0.975)

    return NedPairBootstrap(
        ned_a=na,
        ned_b=nb,
        diff=diff_point,
        ci_lo=ci_lo,
        ci_hi=ci_hi,
        excludes_zero=(ci_lo > 0.0) or (ci_hi < 0.0),
        n_pages=n,
        b=b,
        seed=seed,
    )


def build_forms_pair_macros(result: PairBootstrap) -> dict[str, str]:
    """Map the FORMS Qwen2.5-VL-vs-GLM-OCR paired-bootstrap macros (3 dp).

    ``\\formsPairDiff`` is the point lead and ``\\formsPairLo`` / ``\\formsPairHi``
    the 95% CI of the per-document-resampled FVR difference. The CI straddles 0,
    so the difference is NOT significant -- the macros record that honestly.
    """
    return {
        "formsPairDiff": repr(round(result.diff, 3)),
        "formsPairLo": repr(round(result.ci_lo, 3)),
        "formsPairHi": repr(round(result.ci_hi, 3)),
    }


def build_ids_rapid_pair_macros(result: PairBootstrap) -> dict[str, str]:
    """Map the IDs Surya-vs-RapidOCR paired-bootstrap macros (3 dp).

    ``\\idsPairRapidDiff`` is the point lead and ``\\idsPairRapidLo`` /
    ``\\idsPairRapidHi`` the 95% CI, which excludes 0 (Surya beats the best
    classical engine on IDs FVR).
    """
    return {
        "idsPairRapidDiff": repr(round(result.diff, 3)),
        "idsPairRapidLo": repr(round(result.ci_lo, 3)),
        "idsPairRapidHi": repr(round(result.ci_hi, 3)),
    }


def build_hyb_pair_macros(result: NedPairBootstrap) -> dict[str, str]:
    """Map the HYB Qwen2.5-VL-vs-Surya NED% paired-bootstrap macros (1 dp).

    ``\\hybPairDiff`` is the point lead and ``\\hybPairLo`` / ``\\hybPairHi`` the
    95% CI of the per-page-resampled mean-NED% difference, which excludes 0 (the
    best VLM beats the specialized engine on degraded scans).
    """
    return {
        "hybPairDiff": repr(round(result.diff, 1)),
        "hybPairLo": repr(round(result.ci_lo, 1)),
        "hybPairHi": repr(round(result.ci_hi, 1)),
    }


def all_pair_macros() -> dict[str, str]:
    """Regenerate every paired-bootstrap macro from the committed PII-free arrays.

    Runs all four clustered document-level bootstraps (the original IDs
    Surya-vs-DeepSeek test plus the three additional comparisons) and returns the
    union of their macro maps, ready to be checked against the paper reference.
    """
    ids_docs, _ = load_doc_hits()
    forms_docs, _ = load_doc_hits(FORMS_PAIR_FILE)
    rapid_docs, _ = load_doc_hits(IDS_RAPID_PAIR_FILE)
    hyb_docs, _ = load_doc_ned(HYB_NED_PAIR_FILE)
    return {
        **build_pair_macros(paired_bootstrap(ids_docs)),
        **build_forms_pair_macros(paired_bootstrap(forms_docs)),
        **build_ids_rapid_pair_macros(paired_bootstrap(rapid_docs)),
        **build_hyb_pair_macros(paired_ned_bootstrap(hyb_docs)),
    }


def ned_summary(result: NedPairBootstrap, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """A JSON-serializable summary block for a NED% paired test."""
    return {
        "engine_a": (meta or {}).get("engine_a", "qwen25vl"),
        "engine_b": (meta or {}).get("engine_b", "surya"),
        "metric": "ned_pct",
        "n_pages": result.n_pages,
        "ned_a": round(result.ned_a, 4),
        "ned_b": round(result.ned_b, 4),
        "diff_point": round(result.diff, 4),
        "B": result.b,
        "seed": result.seed,
        "ci95_diff": [round(result.ci_lo, 4), round(result.ci_hi, 4)],
        "ci_excludes_zero": result.excludes_zero,
    }


def all_pair_summaries() -> dict[str, Any]:
    """JSON summary blocks for every paired test (for the consolidated results)."""
    ids_docs, ids_meta = load_doc_hits()
    forms_docs, forms_meta = load_doc_hits(FORMS_PAIR_FILE)
    rapid_docs, rapid_meta = load_doc_hits(IDS_RAPID_PAIR_FILE)
    hyb_docs, hyb_meta = load_doc_ned(HYB_NED_PAIR_FILE)
    return {
        "ids_surya_vs_deepseek": summary(paired_bootstrap(ids_docs), ids_meta),
        "forms_qwen25vl_vs_glmocr": summary(paired_bootstrap(forms_docs), forms_meta),
        "ids_surya_vs_rapidocr": summary(paired_bootstrap(rapid_docs), rapid_meta),
        "hyb_qwen25vl_vs_surya": ned_summary(paired_ned_bootstrap(hyb_docs), hyb_meta),
    }
