"""Static benchmark configuration: the engine roster, scoring axes, and the
deterministic constants that pin every reported number.

This module is the single source of truth for *what* is scored. All paths are
resolved relative to ``$OCR_BENCH_DATA`` (the committed run of record) so nothing
is hardcoded to a host. The scoring logic lives in :mod:`ocr_bench.scoring`,
:mod:`ocr_bench.degradation`, and :mod:`ocr_bench.aggregate`; this file only
declares the roster and the protocol constants.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# --- deterministic protocol constants (pinned; never change without a re-run) ---
BOOT_SEED = 20260609
BOOT_N = 10_000
WILSON_Z = 1.96

EngineType = Literal["vlm", "classical", "specialized"]
AxisMetric = Literal["fvr", "ned"]


def data_root() -> Path:
    """Root of the committed run of record.

    Defaults to ``<repo>/data`` and is overridable with ``$OCR_BENCH_DATA`` so
    the scorer can point at a fresh-from-scratch run without editing code.
    """
    env = os.environ.get("OCR_BENCH_DATA")
    if env:
        return Path(env).expanduser().resolve()
    return (Path(__file__).resolve().parents[2] / "data").resolve()


@dataclass(frozen=True)
class Engine:
    """One scored OCR engine and its presentation metadata."""

    key: str          # filename suffix, e.g. "qwen25vl" -> *.qwen25vl.txt
    display: str      # paper display name
    type: EngineType
    params: str       # parameter count for VLMs; "-" for detector+recognizer


# Roster order matches the paper tables (by type, then ascending size).
ENGINES: tuple[Engine, ...] = (
    Engine("paddleocrvl", "PaddleOCR-VL", "vlm", "0.9B"),
    Engine("hunyuanocr", "HunyuanOCR", "vlm", "1B"),
    Engine("mineru", "MinerU", "vlm", "1.2B"),
    Engine("deepseekocr", "DeepSeek-OCR", "vlm", "3B"),
    Engine("dotsocr", "dots.ocr", "vlm", "3B"),
    Engine("qwen3vl", "Qwen3-VL", "vlm", "4B"),
    Engine("qwen25vl", "Qwen2.5-VL", "vlm", "7B"),
    Engine("glmocr", "GLM-OCR", "vlm", "9B"),
    Engine("tesseract", "Tesseract", "classical", "-"),
    Engine("easyocr", "EasyOCR", "classical", "-"),
    Engine("doctr", "docTR", "classical", "-"),
    Engine("rapidocr", "RapidOCR", "classical", "-"),
    Engine("paddleocr", "PaddleOCR", "classical", "-"),
    Engine("surya", "Surya", "specialized", "-"),
)

ENGINE_BY_KEY = {e.key: e for e in ENGINES}


@dataclass(frozen=True)
class Axis:
    """One scoring axis: a data subdirectory, a metric, and its gold scheme."""

    key: str                    # "forms" | "ids" | "en" | "rib" | "hyb"
    metric: AxisMetric          # how it is scored
    subdir: str                 # subdirectory under the data root
    n: int                      # number of documents (for assertions)
    note: str = ""


# FVR axes score per-image *.fields.json gold; NED axes score *.gold.txt.
AXES: tuple[Axis, ...] = (
    Axis("forms", "fvr", "forms", 50, "Brazilian forms, image-reconstructed gold"),
    Axis("ids", "fvr", "ids", 50, "Brazilian CNH/RG cards, synthetic structured gold"),
    Axis("en", "fvr", "en", 30, "English forms control (VLMs only)"),
    Axis("rib", "ned", "rib", 200, "clean Portuguese prose (ESTER-Pt RIB)"),
    Axis("hyb", "ned", "hyb", 224, "degraded scans (ESTER-Pt HYB), 8 types x 28 pages"),
)

AXIS_BY_KEY = {a.key: a for a in AXES}

# The eight DocCreator degradation types, in the paper's table order.
DEGRADATION_ORDER: tuple[str, ...] = (
    "Bleed",
    "Blur_HYPERBOLA",
    "CharDeg",
    "Hole",
    "Noise_Gaussian",
    "Noise_SaltAndPepper",
    "Phantom_0.85",
    "Rot_color",
)

# Which axes each engine class is scored on (drives null cells in the macros).
# MinerU is forms-only; the EN control is VLM-only; HYB excludes MinerU and the
# two engines whose HYB run is partial (qwen3vl, glmocr carry no per-degradation
# breakdown but do have an overall NED).
FORMS_ONLY = frozenset({"mineru"})
EN_SCORED = frozenset({"paddleocrvl", "hunyuanocr", "deepseekocr", "dotsocr",
                       "qwen3vl", "qwen25vl", "glmocr"})
HYB_NO_BREAKDOWN = frozenset({"qwen3vl", "glmocr"})
