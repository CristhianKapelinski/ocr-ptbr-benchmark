"""Build every paper table from the scored run of record.

One function per paper table. Each builds its rows from the SAME consolidated
results the LaTeX macros are rendered from (:func:`ocr_bench.aggregate.consolidate`),
so there is a single source of truth -- no number is typed twice. Every builder
returns a :class:`Table` carrying both a readable ASCII rendering and the LaTeX
``tabular`` body, so ``ocr-bench tables`` can print the human view and
``ocr-bench tables --latex`` can emit the paper bodies.

Tables emitted, with the paper table each one backs. The paper's Table 1
(positioning against named benchmarks) and Table 2 (scored sets, gold source and
licenses) are written by hand from the literature and the dataset licenses, so
they are not emitted here; nothing in this module is their source.

  * Local Table 1 -- positioning along qualitative dimensions, from the committed
    ``results/positioning.json``. Context only: it is NOT the paper's Table 1.
  * Local Table 2 -- accuracy by engine (forms / IDs FVR, RIB / HYB NED%) with
    95% CIs, grouped VLM | OCR-engine, 14 engines. Backs paper Table 3.
  * Local Table 3 -- local cost axis: per-page latency (forms / IDs) with params
    and device, two panels (VLM | OCR-engine). Backs paper Table 5.
  * Local Table 4 -- per-degradation NED matrix (14 engines x 8 DocCreator
    types), reusing the HYB ``by_degradation`` breakdown. Backs paper Table 4.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import DEGRADATION_ORDER, ENGINES, Engine

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"
POSITIONING_FILE = RESULTS_DIR / "positioning.json"

DASH = "--"

# Engine device for the cost axis, derived from the engine type so it stays in
# sync with the roster: VLMs and the specialized engine are GPU-served, the
# classical pipelines run on CPU.
_DEVICE = {"vlm": "GPU", "specialized": "GPU", "classical": "CPU"}


@dataclass(frozen=True)
class Table:
    """One paper table rendered two ways from the same data."""

    key: str        # "table1".."table4"
    title: str      # human caption
    text: str       # ASCII rendering (no trailing newline)
    latex: str      # LaTeX tabular body (no trailing newline)


def _fnum(x: float | None, dp: int = 3) -> str:
    """Minimal-float-repr to ``dp`` places, or ``--`` for ``None`` (paper style)."""
    return DASH if x is None else repr(round(x, dp))


def _ci(block: dict[str, Any] | None, dp: int) -> str:
    """``[lo, hi]`` 95% CI string for a score block, or ``--`` when absent."""
    if not block or block.get("ci") is None:
        return DASH
    lo, hi = block["ci"]
    return f"[{_fnum(lo, dp)}, {_fnum(hi, dp)}]"


def _is_engine_only(etype: str) -> bool:
    """OCR-engine panel = classical pipelines + the specialized engine."""
    return etype in ("classical", "specialized")


def _grouped(results: dict[str, dict[str, Any]]) -> tuple[list[Engine], list[Engine]]:
    """Roster split into the (VLM, OCR-engine) panels in paper order."""
    vlm = [e for e in ENGINES if e.type == "vlm"]
    ocr = [e for e in ENGINES if _is_engine_only(e.type)]
    return vlm, ocr


def _ascii_table(headers: list[str], rows: list[list[str]],
                 aligns: list[str] | None = None) -> str:
    """Render a fixed-width ASCII table with a header rule."""
    cols = len(headers)
    aligns = aligns or (["l"] + ["r"] * (cols - 1))
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt(cells: list[str]) -> str:
        out = []
        for i, cell in enumerate(cells):
            out.append(cell.ljust(widths[i]) if aligns[i] == "l"
                       else cell.rjust(widths[i]))
        return "  ".join(out).rstrip()

    rule = "  ".join("-" * w for w in widths)
    lines = [fmt(headers), rule]
    lines.extend(fmt(r) for r in rows)
    return "\n".join(lines)


def _latex_rows(rows: list[list[str]]) -> str:
    """Join cell lists into LaTeX ``a & b \\\\`` rows."""
    return "\n".join(" & ".join(r) + r" \\" for r in rows)


# --------------------------------------------------------------------------- #
# Table 1 -- positioning (qualitative)
# --------------------------------------------------------------------------- #
def table_positioning(_: dict[str, dict[str, Any]] | None = None) -> Table:
    """Qualitative positioning vs related OCR benchmarks.

    Table 1 is not data-driven: it places this benchmark against prior work along
    qualitative axes (Portuguese coverage, document types, the local cost axis).
    Its content lives in a small committed data file so the renderer carries no
    inline prose; if the file is absent the table is skipped with a note.
    """
    title = "Table 1: positioning vs related OCR benchmarks (qualitative)"
    if not POSITIONING_FILE.exists():
        note = ("(qualitative; no results/positioning.json committed -- "
                "this table is static prose in the paper)")
        return Table("table1", title, f"{title}\n{note}", f"% {note}")

    spec = json.loads(POSITIONING_FILE.read_text(encoding="utf-8"))
    headers = [c["title"] for c in spec["columns"]]
    keys = [c["key"] for c in spec["columns"]]
    rows = [[str(row.get(k, "")) for k in keys] for row in spec["rows"]]
    aligns = ["l"] * len(headers)
    text = f"{title}\n" + _ascii_table(headers, rows, aligns)
    latex = _latex_rows([headers] + rows)
    return Table("table1", title, text, latex)


# --------------------------------------------------------------------------- #
# Table 2 -- accuracy by engine
# --------------------------------------------------------------------------- #
def _acc_row(e: Engine, r: dict[str, Any]) -> list[str]:
    forms, ids, rib, hyb = (r.get("forms"), r.get("ids"),
                            r.get("rib"), r.get("hyb"))
    return [
        e.display,
        e.params,
        _fnum(forms["fvr"]) if forms else DASH, _ci(forms, 3),
        _fnum(ids["fvr"]) if ids else DASH, _ci(ids, 3),
        _fnum(rib["ned"], 2) if rib else DASH, _ci(rib, 2),
        _fnum(hyb["ned"], 2) if hyb else DASH, _ci(hyb, 2),
    ]


def table_accuracy(results: dict[str, dict[str, Any]]) -> Table:
    """Table 2: forms/IDs FVR and RIB/HYB NED% with 95% CIs, VLM | OCR-engine."""
    title = ("Table 2: accuracy by engine "
             "(forms FVR, IDs FVR, RIB NED%, HYB NED%; 95% CI)")
    headers = ["Engine", "Params",
               "Forms FVR", "95% CI", "IDs FVR", "95% CI",
               "RIB NED%", "95% CI", "HYB NED%", "95% CI"]
    aligns = ["l", "r"] + ["r"] * 8
    vlm, ocr = _grouped(results)

    text_rows: list[list[str]] = []
    latex_rows: list[list[str]] = []
    for label, group in (("VLM", vlm), ("OCR engine", ocr)):
        text_rows.append([f"-- {label} --"] + [""] * (len(headers) - 1))
        latex_rows.append([rf"\multicolumn{{{len(headers)}}}{{l}}{{\textit{{{label}}}}}"])
        for e in group:
            row = _acc_row(e, results[e.key])
            text_rows.append(row)
            latex_rows.append(row)

    text = f"{title}\n" + _ascii_table(headers, text_rows, aligns)
    latex = _latex_rows([headers] + latex_rows)
    return Table("table2", title, text, latex)


# --------------------------------------------------------------------------- #
# Table 3 -- local cost axis (latency)
# --------------------------------------------------------------------------- #
def _cost_row(e: Engine, r: dict[str, Any]) -> list[str]:
    lat = r.get("latency") or {}
    return [
        e.display,
        e.params,
        _DEVICE.get(e.type, "?"),
        _fnum(lat.get("forms_med"), 2),
        _fnum(lat.get("ids_med"), 2),
    ]


def table_cost(results: dict[str, dict[str, Any]]) -> Table:
    """Table 3: per-page latency (forms / IDs) with params and device.

    Two panels (VLM | OCR-engine), each row carrying the engine's parameter count
    and the device it was timed on (GPU for VLMs and the specialized engine, CPU
    for the classical pipelines).
    """
    title = "Table 3: local cost axis -- per-page latency (s), forms / IDs"
    headers = ["Engine", "Params", "Device", "Forms s/page", "IDs s/page"]
    aligns = ["l", "r", "l", "r", "r"]
    vlm, ocr = _grouped(results)

    text_rows: list[list[str]] = []
    latex_rows: list[list[str]] = []
    for label, group in (("VLM", vlm), ("OCR engine", ocr)):
        text_rows.append([f"-- {label} --"] + [""] * (len(headers) - 1))
        latex_rows.append([rf"\multicolumn{{{len(headers)}}}{{l}}{{\textit{{{label}}}}}"])
        for e in group:
            row = _cost_row(e, results[e.key])
            text_rows.append(row)
            latex_rows.append(row)

    text = f"{title}\n" + _ascii_table(headers, text_rows, aligns)
    latex = _latex_rows([headers] + latex_rows)
    return Table("table3", title, text, latex)


# --------------------------------------------------------------------------- #
# Table 4 -- per-degradation NED matrix
# --------------------------------------------------------------------------- #
def _short_deg(tag: str) -> str:
    """Compact column label for a DocCreator degradation tag."""
    return {
        "Bleed": "Bleed",
        "Blur_HYPERBOLA": "Blur",
        "CharDeg": "CharDeg",
        "Hole": "Hole",
        "Noise_Gaussian": "Gauss",
        "Noise_SaltAndPepper": "S&P",
        "Phantom_0.85": "Phantom",
        "Rot_color": "Rot",
    }.get(tag, tag)


def table_degradation(results: dict[str, dict[str, Any]]) -> Table:
    """Table 4: mean NED% per DocCreator degradation type (14 engines x 8)."""
    title = "Table 4: per-degradation NED% on the HYB axis (8 DocCreator types)"
    headers = ["Engine"] + [_short_deg(d) for d in DEGRADATION_ORDER] + ["Overall"]
    aligns = ["l"] + ["r"] * (len(headers) - 1)

    rows: list[list[str]] = []
    for e in ENGINES:
        hyb = results[e.key].get("hyb")
        if not hyb:
            continue
        bd = hyb.get("by_degradation") or {}
        cells = [_fnum(bd.get(d), 1) for d in DEGRADATION_ORDER]
        rows.append([e.display, *cells, _fnum(hyb.get("ned"), 2)])

    text = f"{title}\n" + _ascii_table(headers, rows, aligns)
    latex = _latex_rows([headers] + rows)
    return Table("table4", title, text, latex)


# --------------------------------------------------------------------------- #
# Registry + driver
# --------------------------------------------------------------------------- #
BUILDERS = (
    table_positioning,
    table_accuracy,
    table_cost,
    table_degradation,
)


def build_all(results: dict[str, dict[str, Any]]) -> list[Table]:
    """Build every paper table from one consolidated-results dict."""
    return [build(results) for build in BUILDERS]


def render_all(results: dict[str, dict[str, Any]], latex: bool = False) -> str:
    """Render every table back to back (ASCII by default, LaTeX bodies if asked)."""
    tables = build_all(results)
    blocks = []
    for t in tables:
        if latex:
            blocks.append(f"% {t.title}\n{t.latex}")
        else:
            blocks.append(t.text)
    return "\n\n".join(blocks) + "\n"
