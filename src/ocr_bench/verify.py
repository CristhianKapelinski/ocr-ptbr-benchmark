"""Assert the regenerated macros match the paper's committed reference.

Parses ``results/results_macros.reference.tex`` (the macro file the paper
compiles) into a name -> value map, then compares it field by field with the
macros regenerated from the run of record. Numeric cells must match exactly at
the paper's printed precision; ``--`` cells must agree. Any mismatch is a
reproduction failure and is reported with both values.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .macros import build_macros

_CMD = re.compile(r"\\newcommand\{\\([A-Za-z]+)\}\{([^}]*)\}")

REFERENCE = (
    Path(__file__).resolve().parents[2] / "results" / "results_macros.reference.tex"
)

# Confidence-interval bounds are checked within a stated tolerance; every point
# estimate (FVR, NED mean, latency, per-degradation) is checked exactly.
#   - NED bounds (rib/hyb Lo/Hi) are bootstrap, reproducible only up to the
#     resampling order that the original consolidated results did not record:
#     tolerance 0.15 pp on the 0-100 NED scale.
#   - FVR bounds (forms/ids/en Lo/Hi) are analytic Wilson and reproduce to a
#     1e-3 last-digit rounding difference left by the original two-step
#     (4-dp then 3-dp) rounding in the consolidation pipeline.
_NED_CI = re.compile(r"^(rib|hyb)[A-Za-z]+?(Lo|Hi)$")
_FVR_CI = re.compile(r"^(forms|ids|en)[A-Za-z]+?(Lo|Hi)$")
NED_TOL = 0.15
FVR_TOL = 0.0011


@dataclass(frozen=True)
class Mismatch:
    name: str
    generated: str
    reference: str


def parse_reference(path: Path = REFERENCE) -> dict[str, str]:
    """Parse a ``results_macros.tex`` into ``{macro_name: value}``."""
    return {m.group(1): m.group(2) for m in _CMD.finditer(path.read_text(encoding="utf-8"))}


def _norm_value(v: str) -> str:
    """Canonicalize a macro value for comparison (numbers compared as floats)."""
    v = v.strip()
    try:
        return repr(round(float(v), 6))
    except ValueError:
        return v


def compare(results: dict[str, dict[str, Any]],
            reference: dict[str, str] | None = None) -> list[Mismatch]:
    """Return the mismatches between regenerated macros and the reference.

    Only macros that the analysis regenerates are checked; prose-framing macros
    in the reference (best-engine names, ranges) are out of scope here and are
    validated separately by the figure/summary layer.
    """
    ref = reference if reference is not None else parse_reference()
    generated = build_macros(results)
    mismatches: list[Mismatch] = []
    for name, gen in generated.items():
        if name not in ref:
            mismatches.append(Mismatch(name, gen, "<absent from reference>"))
            continue
        if _norm_value(gen) == _norm_value(ref[name]):
            continue
        tol = NED_TOL if _NED_CI.match(name) else (FVR_TOL if _FVR_CI.match(name) else None)
        if tol is not None:
            try:
                if abs(float(gen) - float(ref[name])) <= tol:
                    continue
            except ValueError:
                pass
        mismatches.append(Mismatch(name, gen, ref[name]))
    return mismatches
