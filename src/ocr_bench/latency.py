"""Per-page latency: medians recomputed from the committed run manifests.

GPU-served engines (the VLMs and Surya) carry a ``_run*.json`` manifest per
axis, so their median seconds/page is recomputed offline from those manifests.
The CPU classical pipelines were timed once in a separate load-once cost run;
their measured medians are committed as constants in ``data/cost/`` and read
back here, because their per-page run manifests are not part of the run of
record. Both sources are explicit so a reviewer can see exactly where each
latency cell comes from.
"""
from __future__ import annotations

import json
from pathlib import Path

from .config import data_root
from .io import load_latency_median

# Manifest filename per axis (engine substituted in). Forms uses the _run50_
# naming; Surya writes _run_surya.json on every axis; rib/hyb store the qwen2.5
# manifest with a _txt suffix.
_AXIS_MANIFEST = {
    "forms": "_run50_{engine}.json",
    "ids": "_run_{engine}.json",
    "rib": "_run_{engine}.json",
    "hyb": "_run_{engine}.json",
}
_NAME_OVERRIDES = {
    ("forms", "surya"): "_run_surya.json",
    ("rib", "qwen25vl"): "_run_qwen25vl_txt.json",
    ("hyb", "qwen25vl"): "_run_qwen25vl_txt.json",
}

# Classical CPU engines timed load-once on the reference machine (median s/page).
# Tesseract forms latency is recomputed from its committed manifest; the rest are
# the measured medians reported in the paper.
_CLASSICAL_COST_FILE = "cost/_classical_latency.json"


def _manifest(axis: str, engine: str) -> Path | None:
    pattern = _AXIS_MANIFEST.get(axis)
    if pattern is None:
        return None
    name = _NAME_OVERRIDES.get((axis, engine), pattern.format(engine=engine))
    return data_root() / axis / name


def gpu_latency(axis: str, engine: str) -> float | None:
    """Median s/page for a GPU-served engine, recomputed from its manifest."""
    m = _manifest(axis, engine)
    return None if m is None else load_latency_median(m)


def classical_latency() -> dict[str, dict[str, float | None]]:
    """Measured CPU medians for the classical pipelines, keyed by engine then axis."""
    path = data_root() / _CLASSICAL_COST_FILE
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
