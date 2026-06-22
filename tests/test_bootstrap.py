"""The IDs paired document-level bootstrap reproduces the paper's significance test.

Recomputes the clustered paired bootstrap from the committed PII-free hit array
(``data/ids_pair_hits.json``) and asserts it regenerates the paper macros
exactly: the marginals (Surya 0.921, DeepSeek-OCR 0.864), the +0.057 lead, and
the 95% CI [0.023, 0.089] that excludes 0 (B=10000, seed=20260609).
"""
from __future__ import annotations

from ocr_bench.bootstrap import (
    build_pair_macros,
    load_doc_hits,
    paired_bootstrap,
)
from ocr_bench.config import BOOT_N, BOOT_SEED
from ocr_bench.verify import compare_pair, parse_reference


def test_hit_array_is_paired_and_pii_free():
    docs, meta = load_doc_hits()
    assert meta["n_docs"] == 50
    assert meta["n_fields"] == 354
    assert meta["engine_a"] == "surya" and meta["engine_b"] == "deepseekocr"
    assert len(docs) == 50
    # Every recorded value is a binary hit; no field text, only integers.
    for d in docs:
        assert all(h in (0, 1) for h in d.hits_a)
        assert all(h in (0, 1) for h in d.hits_b)
    assert sum(len(d.hits_a) for d in docs) == 354
    # Marginal recovered counts behind the published FVRs.
    assert sum(sum(d.hits_a) for d in docs) == 326  # 326/354 = 0.921
    assert sum(sum(d.hits_b) for d in docs) == 306  # 306/354 = 0.864


def test_paired_bootstrap_regenerates_ci():
    result = paired_bootstrap(b=BOOT_N, seed=BOOT_SEED)
    assert round(result.fvr_a, 3) == 0.921
    assert round(result.fvr_b, 3) == 0.864
    assert round(result.ci_lo, 3) == 0.023
    assert round(result.ci_hi, 3) == 0.089
    assert result.excludes_zero
    macros = build_pair_macros(result)
    assert macros == {
        "idsPairSurya": "0.921",
        "idsPairDeepSeek": "0.864",
        "idsPairDiff": "0.057",
        "idsPairLo": "0.023",
        "idsPairHi": "0.089",
    }


def test_pair_macros_match_paper_reference():
    macros = build_pair_macros(paired_bootstrap())
    mismatches = compare_pair(macros, parse_reference())
    assert not mismatches, "\n".join(
        f"\\{m.name}: generated={m.generated!r} reference={m.reference!r}"
        for m in mismatches
    )
