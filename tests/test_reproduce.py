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
