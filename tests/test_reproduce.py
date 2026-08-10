"""Integration test: the run of record reproduces the paper's reference macros.

This is the same assertion the ``reproduce`` CLI makes, run over the committed
data. It is the test a reviewer can use to confirm the Reproducible seal offline.
"""
from __future__ import annotations

from ocr_bench.aggregate import consolidate
from ocr_bench.verify import compare


def test_regenerated_macros_match_paper_reference():
    results = consolidate()
    mismatches = compare(results)
    assert not mismatches, "\n".join(
        f"\\{m.name}: generated={m.generated!r} reference={m.reference!r}"
        for m in mismatches
    )


def test_axis_document_counts():
    results = consolidate()
    # Forms FVR axis: 50 forms scored for Qwen2.5-VL.
    assert results["qwen25vl"]["rib"]["n"] == 200
    assert results["qwen25vl"]["hyb"]["n"] == 224
    # IDs axis micro denominator is 354 scored fields.
    assert results["surya"]["ids"]["total"] == 354


def test_mineru_scored_on_every_axis_and_degradation_set_covers_all_engines():
    results = consolidate()
    # MinerU is no longer forms-only: it now carries IDs/RIB/HYB cells.
    mineru = results["mineru"]
    assert mineru["ids"]["total"] == 354  # from the committed PII-free hit array
    assert mineru["rib"]["n"] == 200
    assert mineru["hyb"]["n"] == 224
    assert mineru["en"]["total"] == 448  # EN control added after the original run
    # The degradation breakdown covers every engine. qwen3vl and glmocr used to be
    # excluded here on the false premise that their HYB run carried no breakdown;
    # it does, and it reproduces the paper's Table 5 exactly.
    covered = sum(
        1 for k, r in results.items()
        if (r.get("hyb") or {}).get("by_degradation")
    )
    assert covered == len(results) == 14
    assert "by_degradation" in mineru["hyb"]
