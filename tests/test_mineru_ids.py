"""MinerU's IDs FVR reproduces from a committed PII-free hit array.

The identity raw data is never redistributed, so MinerU's identity-document FVR is recomputed
from ``data/ids_mineru_hits.json`` (a 0/1 hit per scored field, no field text)
exactly as the other engines' IDs FVR is computed from raw values. This asserts
the array is PII-free and that the no-GPU re-score regenerates the paper's
``\\idsMineru`` cell, its 95% Wilson CI, and ``\\minerEmptyIDs``.
"""
from __future__ import annotations

from ocr_bench.mineru_ids import load_hits, score_ids
from ocr_bench.verify import compare, parse_reference


def test_mineru_ids_hits_are_binary_and_pii_free():
    hits, meta = load_hits()
    assert meta["engine"] == "mineru"
    assert meta["axis"] == "ids" and meta["metric"] == "fvr"
    assert meta["n_docs"] == 50
    assert meta["n_fields"] == 354
    assert meta["empty_docs"] == 19
    # Only integers: every recorded value is a binary hit, no field text.
    assert len(hits) == 354
    assert all(h in (0, 1) for h in hits)
    assert sum(hits) == 164  # 164/354 = 0.463
    # Every committed [doc, hit] row carries only integers.
    for doc, hit in meta["pairs"]:
        assert isinstance(doc, int) and isinstance(hit, int)
        assert hit in (0, 1)


def test_mineru_ids_score_regenerates_fvr_and_wilson():
    block = score_ids()
    assert block is not None
    assert block["fvr"] == 0.463
    assert block["recovered"] == 164
    assert block["total"] == 354
    assert block["empty_docs"] == 19
    # Analytic Wilson 95% CI, recomputed from the committed hits.
    assert block["ci"] == [0.412, 0.515]


def test_mineru_macros_match_paper_reference():
    # The MinerU IDs/RIB/HYB cells and \minerEmptyIDs are part of the standard
    # macro comparison; assert none of them mismatch the paper reference.
    from ocr_bench.aggregate import consolidate

    ref = parse_reference()
    mismatches = [m for m in compare(consolidate(), ref)
                  if "Mineru" in m.name or m.name == "minerEmptyIDs"]
    assert not mismatches, "\n".join(
        f"\\{m.name}: generated={m.generated!r} reference={m.reference!r}"
        for m in mismatches
    )
