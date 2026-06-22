"""Unit tests for the metric primitives (no network, no run of record needed)."""
from __future__ import annotations

from ocr_bench.scoring import (
    _levenshtein_py,
    alnum_norm,
    bootstrap_ci,
    date_candidates,
    levenshtein,
    ned,
    ned_pct,
    text_norm,
    wilson_ci,
)


def test_alnum_norm_strips_punctuation_and_case():
    assert alnum_norm("171.613.476-53") == "17161347653"
    assert alnum_norm("Hanna Zalc Berla") == "hannazalcberla"
    assert alnum_norm(None) == ""


def test_text_norm_collapses_whitespace_and_lowercases():
    assert text_norm("  A  B\nC ") == "a b c"


def test_levenshtein_basic():
    assert levenshtein("abc", "abc") == 0
    assert levenshtein("", "abc") == 3
    assert levenshtein("kitten", "sitting") == 3


def test_levenshtein_backend_matches_reference():
    cases = [("", ""), ("a", ""), ("kitten", "sitting"),
             ("the quick brown fox", "teh quikc brown fax"),
             ("transcrição fiel", "transcricao  fiel")]
    for a, b in cases:
        assert levenshtein(a, b) == _levenshtein_py(a, b)


def test_ned_and_pct():
    assert ned("abc", "abc") == 0.0
    assert ned_pct("abc", "abc") == 100.0
    # empty gold yields None
    assert ned("x", "") is None
    assert ned_pct("x", "") is None
    # half-wrong short string is bounded in [0, 1]
    v = ned("ac", "abc")
    assert 0.0 < v <= 1.0


def test_date_candidates_expands_iso_to_printed_formats():
    cands = date_candidates("1997-03-25")
    assert alnum_norm("25/03/1997") in cands
    assert alnum_norm("1997-03-25") in cands
    # non-date value is returned as-is, normalized
    assert date_candidates("B") == {"b"}


def test_wilson_ci_monotone_and_bounded():
    lo, hi = wilson_ci(326, 354)
    assert 0.0 < lo < 0.921 < hi < 1.0
    assert wilson_ci(0, 0) == (0.0, 0.0)


def test_bootstrap_ci_is_deterministic():
    vals = [90.0, 92.0, 95.0, 97.0, 99.0, 80.0, 100.0, 88.0]
    assert bootstrap_ci(vals) == bootstrap_ci(vals)
    assert bootstrap_ci([1.0]) == (None, None)
