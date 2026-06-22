"""The paired document-level bootstraps reproduce the paper's significance tests.

Recomputes each clustered paired bootstrap from its committed PII-free array and
asserts it regenerates the paper macros exactly (B=10000, seed=20260609):

  * IDs Surya vs DeepSeek-OCR (``data/ids_pair_hits.json``): marginals
    0.921 / 0.864, +0.057 lead, 95% CI [0.023, 0.089], excludes 0.
  * FORMS Qwen2.5-VL vs GLM-OCR (``data/forms_pair_hits.json``): +0.005,
    95% CI [-0.010, 0.019], straddles 0 (NOT significant).
  * IDs Surya vs RapidOCR (``data/ids_pair_hits_surya_rapidocr.json``): +0.051,
    95% CI [0.023, 0.079], excludes 0.
  * HYB Qwen2.5-VL vs Surya, NED% (``data/hyb_pair_ned.json``): +3.6,
    95% CI [1.9, 5.6], excludes 0.
"""
from __future__ import annotations

from ocr_bench.bootstrap import (
    FORMS_PAIR_FILE,
    HYB_NED_PAIR_FILE,
    IDS_RAPID_PAIR_FILE,
    all_pair_macros,
    build_forms_pair_macros,
    build_hyb_pair_macros,
    build_ids_rapid_pair_macros,
    build_pair_macros,
    load_doc_hits,
    load_doc_ned,
    paired_bootstrap,
    paired_ned_bootstrap,
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


def test_new_pair_arrays_are_paired_and_pii_free():
    # FVR pair files: same schema as the IDs file, binary hits only.
    for path, n_fields in ((FORMS_PAIR_FILE, 1428), (IDS_RAPID_PAIR_FILE, 354)):
        docs, meta = load_doc_hits(path)
        assert meta["n_docs"] == 50
        assert meta["n_fields"] == n_fields
        assert sum(len(d.hits_a) for d in docs) == n_fields
        for d in docs:
            assert all(h in (0, 1) for h in d.hits_a)
            assert all(h in (0, 1) for h in d.hits_b)
    # NED pair file: per-page NED% floats in [0, 100], one pair per page.
    ned_docs, ned_meta = load_doc_ned(HYB_NED_PAIR_FILE)
    assert ned_meta["n_pages"] == 224
    assert len(ned_docs) == 224
    for d in ned_docs:
        assert 0.0 <= d.ned_a <= 100.0
        assert 0.0 <= d.ned_b <= 100.0


def test_forms_pair_not_significant():
    result = paired_bootstrap(load_doc_hits(FORMS_PAIR_FILE)[0], b=BOOT_N, seed=BOOT_SEED)
    assert not result.excludes_zero  # CI straddles 0: the two VLMs are tied.
    assert build_forms_pair_macros(result) == {
        "formsPairDiff": "0.005",
        "formsPairLo": "-0.01",
        "formsPairHi": "0.019",
    }


def test_ids_rapid_pair_significant():
    result = paired_bootstrap(load_doc_hits(IDS_RAPID_PAIR_FILE)[0], b=BOOT_N, seed=BOOT_SEED)
    assert result.excludes_zero
    assert build_ids_rapid_pair_macros(result) == {
        "idsPairRapidDiff": "0.051",
        "idsPairRapidLo": "0.023",
        "idsPairRapidHi": "0.079",
    }


def test_hyb_ned_pair_significant():
    result = paired_ned_bootstrap(load_doc_ned(HYB_NED_PAIR_FILE)[0], b=BOOT_N, seed=BOOT_SEED)
    assert result.excludes_zero
    assert build_hyb_pair_macros(result) == {
        "hybPairDiff": "3.6",
        "hybPairLo": "1.9",
        "hybPairHi": "5.6",
    }


def test_all_pair_macros_match_paper_reference():
    mismatches = compare_pair(all_pair_macros(), parse_reference())
    assert not mismatches, "\n".join(
        f"\\{m.name}: generated={m.generated!r} reference={m.reference!r}"
        for m in mismatches
    )
