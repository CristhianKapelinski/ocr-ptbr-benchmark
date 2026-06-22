"""The paper tables are emitted and stay consistent with the reference macros.

``ocr-bench tables`` builds every paper table from the same consolidated results
the LaTeX macros are rendered from, so the tables must carry exactly the numbers
the paper compiles. This asserts (a) every table is produced with both a readable
and a LaTeX rendering, and (b) the accuracy, cost and per-degradation cells equal
the committed reference macros -- the single-source-of-truth check.
"""
from __future__ import annotations

from ocr_bench.aggregate import consolidate
from ocr_bench.config import DEGRADATION_ORDER, ENGINES
from ocr_bench.macros import TAG, build_macros
from ocr_bench.tables import (
    BUILDERS,
    build_all,
    render_all,
    table_accuracy,
    table_cost,
    table_degradation,
)


def test_every_paper_table_is_built_with_both_renderings():
    results = consolidate()
    tables = build_all(results)
    assert [t.key for t in tables] == ["table1", "table2", "table3", "table4"]
    assert len(tables) == len(BUILDERS) == 4
    for t in tables:
        assert t.text.strip(), f"{t.key} has empty text rendering"
        assert t.latex.strip(), f"{t.key} has empty latex rendering"
    # The driver concatenates them; the LaTeX form differs from the readable one.
    assert render_all(results) != render_all(results, latex=True)


def test_accuracy_table_cells_match_regenerated_macros():
    # Single source of truth: the table cells are formatted exactly like the
    # data-driven macros (both from the same consolidate() aggregate via the same
    # minimal-float repr), and those macros are asserted equal to the paper
    # reference in test_reproduce / verify.compare. So every FVR/NED point
    # estimate the macros carry must appear verbatim in Table 2.
    results = consolidate()
    macros = build_macros(results)
    text = table_accuracy(results).text
    for e in ENGINES:
        tag = TAG[e.key]
        for macro in (f"forms{tag}", f"ids{tag}", f"rib{tag}", f"hyb{tag}"):
            val = macros.get(macro)
            if val and val != "--":
                assert val in text, f"\\{macro}={val} missing from Table 2"


def test_cost_table_cells_match_regenerated_macros():
    results = consolidate()
    macros = build_macros(results)
    text = table_cost(results).text
    for e in ENGINES:
        tag = TAG[e.key]
        for macro in (f"latF{tag}", f"latI{tag}"):
            val = macros.get(macro)
            if val and val != "--":
                assert val in text, f"\\{macro}={val} missing from Table 3"
    # The device column is type-derived: VLMs/Surya on GPU, classical on CPU.
    assert "GPU" in text and "CPU" in text


def test_degradation_table_matches_consolidated_breakdown():
    results = consolidate()
    table = table_degradation(results)
    # Header carries the 8 DocCreator types plus an overall column.
    assert len(DEGRADATION_ORDER) == 8
    # Spot-check a known cell against the live breakdown (single source of truth).
    qwen_hyb = results["qwen25vl"]["hyb"]
    assert repr(round(qwen_hyb["ned"], 2)) in table.text
    assert repr(round(qwen_hyb["by_degradation"]["Hole"], 1)) in table.text
    # The two partial-HYB engines appear with dashes, not numbers, in the matrix.
    assert "Qwen3-VL" in table.text and "GLM-OCR" in table.text


def test_positioning_table_is_qualitative_and_pii_free():
    results = consolidate()
    table = build_all(results)[0]
    assert table.key == "table1"
    # Qualitative dimensions only; the file ships no engine scores.
    assert "PT-BR" in table.text
    assert "This benchmark" in table.text
