"""Console entry point for the OCR PT-BR benchmark reproduction.

Subcommands:
  score      Score the run of record; write results/consolidated_results.json.
  macros     Regenerate the data-driven LaTeX macros from the scored results.
  matrix     Print the per-degradation NED matrix (HYB axis).
  figure     Regenerate fig_frontier.pdf (needs the [figure] extra).
  reproduce  Run the full no-GPU path and ASSERT the regenerated numbers match
             the paper's committed reference; non-zero exit on any mismatch.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .aggregate import consolidate
from .bootstrap import (
    build_pair_macros,
    load_doc_hits,
    paired_bootstrap,
)
from .bootstrap import (
    summary as pair_summary,
)
from .config import DEGRADATION_ORDER, ENGINES, data_root
from .macros import build_macros, render_tex
from .verify import compare, compare_pair, parse_reference

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _consolidated_payload(results: dict[str, Any]) -> dict[str, Any]:
    """Compose the on-disk consolidated results: per-engine blocks plus the
    paired IDs bootstrap summary, kept under a reserved ``_``-prefixed key so the
    macro/figure layers (which iterate engine keys) never see it."""
    docs, meta = load_doc_hits()
    return {**results, "_ids_pair_bootstrap": pair_summary(paired_bootstrap(docs), meta)}


def _cmd_score(_: argparse.Namespace) -> int:
    results = consolidate()
    out = RESULTS_DIR / "consolidated_results.json"
    _write(out, json.dumps(_consolidated_payload(results), indent=2, ensure_ascii=False) + "\n")
    print(f"scored {len(ENGINES)} engines over {data_root()} -> {out}")
    return 0


def _cmd_macros(_: argparse.Namespace) -> int:
    results = consolidate()
    pair_macros = build_pair_macros(paired_bootstrap())
    out = RESULTS_DIR / "results_macros.generated.tex"
    _write(out, render_tex(results, pair_macros))
    print(f"wrote {out}")
    return 0


def _cmd_matrix(_: argparse.Namespace) -> int:
    results = consolidate()
    width = 9
    cols = "".join(d[:width].rjust(width + 1) for d in DEGRADATION_ORDER)
    header = "engine".ljust(14) + cols + "   overall"
    print(header)
    print("-" * len(header))
    for e in ENGINES:
        hyb = results[e.key].get("hyb")
        if not hyb or "by_degradation" not in hyb:
            continue
        cells = []
        for d in DEGRADATION_ORDER:
            v = hyb["by_degradation"].get(d)
            cells.append(("--" if v is None else f"{v:.1f}").rjust(width + 1))
        print(e.key.ljust(14) + "".join(cells) + f"   {hyb['ned']:.1f}")
    return 0


def _cmd_figure(_: argparse.Namespace) -> int:
    from .figure import render
    results = consolidate()
    out = render(results, RESULTS_DIR / "fig_frontier.pdf")
    print(f"wrote {out}")
    return 0


def _report_mismatches(mismatches: list[Any]) -> None:
    print(f"\n  {len(mismatches)} mismatch(es):", file=sys.stderr)
    for mm in mismatches:
        print(f"    \\{mm.name}: generated={mm.generated!r} reference={mm.reference!r}",
              file=sys.stderr)


def _cmd_reproduce(args: argparse.Namespace) -> int:
    print(f"[1/5] scoring run of record at {data_root()} ...")
    results = consolidate()

    print("[2/5] recomputing the paired IDs document-level bootstrap ...")
    docs, meta = load_doc_hits()
    pair = paired_bootstrap(docs)
    pair_macros = build_pair_macros(pair)
    payload = {**results, "_ids_pair_bootstrap": pair_summary(pair, meta)}
    _write(RESULTS_DIR / "consolidated_results.json",
           json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"      Surya {pair.fvr_a:.3f} vs DeepSeek-OCR {pair.fvr_b:.3f}; "
          f"diff {pair_macros['idsPairDiff']} "
          f"95% CI [{pair_macros['idsPairLo']}, {pair_macros['idsPairHi']}] "
          f"(B={pair.b}, seed={pair.seed}), excludes 0: {pair.excludes_zero}")

    print("[3/5] regenerating data-driven LaTeX macros ...")
    _write(RESULTS_DIR / "results_macros.generated.tex",
           render_tex(results, pair_macros))

    print("[4/5] asserting regenerated macros match the paper reference ...")
    reference = parse_reference()
    mismatches = compare(results, reference) + compare_pair(pair_macros, reference)
    n_macros = len(build_macros(results)) + len(pair_macros)
    if mismatches:
        _report_mismatches(mismatches)
        print(f"\nFAIL: {len(mismatches)}/{n_macros} regenerated macros differ "
              "from the paper reference.", file=sys.stderr)
        return 1
    print(f"      OK: all {n_macros} regenerated macros match "
          "results_macros.reference.tex")
    print("      (point estimates exact; CI bounds within the stated tolerance, "
          "see docs/PROTOCOL.md)")
    if not pair.excludes_zero:
        print("\nFAIL: the IDs paired bootstrap CI no longer excludes 0.",
              file=sys.stderr)
        return 1

    if args.figure:
        print("[5/5] regenerating fig_frontier.pdf ...")
        from .figure import render
        render(results, RESULTS_DIR / "fig_frontier.pdf")
    else:
        print("[5/5] skipping figure (pass --figure with the [figure] extra to draw it)")

    print("\nPASS: reproduced the paper's numbers from the committed run of record.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ocr-bench", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("score", help="score the run of record").set_defaults(func=_cmd_score)
    sub.add_parser("macros", help="regenerate LaTeX macros").set_defaults(func=_cmd_macros)
    sub.add_parser("matrix", help="print per-degradation NED matrix").set_defaults(func=_cmd_matrix)
    sub.add_parser("figure", help="regenerate fig_frontier.pdf").set_defaults(func=_cmd_figure)
    rp = sub.add_parser("reproduce", help="score, regenerate, and assert against the paper")
    rp.add_argument("--figure", action="store_true", help="also redraw fig_frontier.pdf")
    rp.set_defaults(func=_cmd_reproduce)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
