"""OCR PT-BR benchmark: offline scoring and paper-number reproduction.

The public surface is the CLI (:func:`ocr_bench.cli.main`) and the scoring
primitives in :mod:`ocr_bench.scoring`. See the package modules for the
analysis pipeline: config -> io -> scoring/degradation/latency -> aggregate ->
macros/tables/figure -> verify.
"""
__version__ = "1.0.0"
