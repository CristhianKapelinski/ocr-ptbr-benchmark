"""Regenerate ``fig_frontier``: field-value recall against processing time.

Two panels, Brazilian forms (left) and identity documents (right). x is the
median seconds per page on a logarithmic scale, y is field-value recall (FVR).
Marker SHAPE encodes engine type and nothing else: VLM is a circle, OCR engine
is a square. Surya is an OCR engine and gets the same square as the rest; it is
not a separate marker category. The dashed line is the Pareto frontier, the
engines no other beats on both higher recall and lower time.

Everything plotted is read from the consolidated results, latencies included
(the classical engines carry theirs in the same ``latency`` block), so the
figure tracks the numbers the paper reports. Matplotlib is an optional
dependency, pulled in only by the ``[figure]`` extra.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import ENGINE_BY_KEY

# Two engine types only: VLM (circle) and OCR engine (square). "classical" and
# "specialized" (Surya) are both OCR engines and share the square.
_MARKER = {"vlm": "o"}
_MARKER_DEFAULT = "s"
_MARKER_SIZE = {"o": 95, "s": 85}

# Stable per-engine colors, keyed by display name.
_COLOR = {
    "PaddleOCR-VL": "#66a61e", "HunyuanOCR": "#1b7837", "MinerU": "#a6761d",
    "DeepSeek-OCR": "#7570b3", "dots.ocr": "#e7298a", "Qwen3-VL": "#e6ab02",
    "Qwen2.5-VL": "#d95f02", "GLM-OCR": "#1f78b4", "Surya": "#e31a1c",
    "Tesseract": "#8c510a", "EasyOCR": "#01665e", "docTR": "#762a83",
    "RapidOCR": "#35978f", "PaddleOCR": "#bf812d",
}

# Hand-tuned label offsets (in points) to de-collide; everything else is data.
_FORMS_OFF = {
    "Qwen2.5-VL": (7, 4), "GLM-OCR": (-7, 5), "Surya": (-7, 6),
    "dots.ocr": (-7, 7), "MinerU": (-7, 7), "Qwen3-VL": (7, -3),
    "DeepSeek-OCR": (-7, -11), "HunyuanOCR": (7, -3),
    "Tesseract": (-7, 6), "EasyOCR": (7, 4), "docTR": (7, -3),
    "RapidOCR": (7, 4), "PaddleOCR": (7, -3),
}
_IDS_OFF = {
    "Surya": (7, 5), "DeepSeek-OCR": (-9, 16), "Qwen2.5-VL": (7, 6),
    "GLM-OCR": (2, 14), "HunyuanOCR": (-7, -11), "dots.ocr": (-7, 6),
    "Qwen3-VL": (7, 4), "PaddleOCR-VL": (-7, 6),
    "Tesseract": (7, 4), "EasyOCR": (7, 4), "docTR": (-7, -11),
    "RapidOCR": (7, 16), "PaddleOCR": (7, -3),
}

# axis key, panel title, y limits, x limits, x ticks, label offsets
_PANELS = (
    ("forms", "Brazilian forms", (0.74, 1.00), (0.55, 16),
     [0.8, 1, 2, 3, 5, 8, 11], _FORMS_OFF),
    ("ids", "Identity documents", (0.18, 0.97), (0.13, 32),
     [0.2, 0.5, 1, 2, 5, 10, 20], _IDS_OFF),
)


def _points(results: dict[str, dict[str, Any]], axis: str) -> list[tuple[float, float, str, str]]:
    """(latency, fvr, type, display) for engines with both on this axis."""
    lat_key = "forms_med" if axis == "forms" else "ids_med"
    pts = []
    for key, r in results.items():
        block = r.get(axis)
        lat = (r.get("latency") or {}).get(lat_key)
        if not block or block.get("fvr") is None or lat is None:
            continue
        pts.append((float(lat), float(block["fvr"]), r["type"], ENGINE_BY_KEY[key].display))
    return pts


def _pareto_xy(points: list[tuple[float, float, str, str]]) -> tuple[list[float], list[float]]:
    """Pareto staircase (min time, max recall) as an x,y polyline to plot."""
    xy = [(x, y) for x, y, *_ in points]
    opt = [
        (xi, yi) for i, (xi, yi) in enumerate(xy)
        if not any(xj <= xi and yj >= yi and (xj < xi or yj > yi)
                   for j, (xj, yj) in enumerate(xy) if j != i)
    ]
    opt.sort()
    xs: list[float] = []
    ys: list[float] = []
    for k, (x, y) in enumerate(opt):
        if k:                        # vertical riser, then horizontal tread
            xs.append(x)
            ys.append(ys[-1])
        xs.append(x)
        ys.append(y)
    return xs, ys


def render(results: dict[str, dict[str, Any]], out_path: Path, n_docs: int = 50) -> Path:
    """Write ``fig_frontier`` (PDF) and return its path."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FixedLocator, NullLocator, ScalarFormatter

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.2))
    for ax, (axis, title, ylim, xlim, ticks, offsets) in zip(axes, _PANELS, strict=True):
        pts = _points(results, axis)
        fx, fy = _pareto_xy(pts)
        ax.plot(fx, fy, "--", color="0.55", lw=1.4, zorder=1)
        for lat, fvr, etype, name in pts:
            mk = _MARKER.get(etype, _MARKER_DEFAULT)
            ax.scatter(lat, fvr, s=_MARKER_SIZE[mk], marker=mk,
                       facecolor=_COLOR.get(name, "0.5"), edgecolor="black",
                       linewidths=0.7, alpha=0.95, zorder=3)
            dx, dy = offsets.get(name, (8, 4))
            ax.annotate(name, (lat, fvr), textcoords="offset points",
                        xytext=(dx, dy), fontsize=9.5, color="0.10",
                        ha="left" if dx >= 0 else "right",
                        va="bottom" if dy >= 0 else "top", zorder=5)
        ax.set_xscale("log")
        ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_major_formatter(ScalarFormatter())
        ax.xaxis.set_minor_locator(NullLocator())
        ax.set_xlabel("Median processing time (s/page, log scale)", fontsize=12)
        ax.set_ylabel("Field-value recall (FVR)", fontsize=12)
        ax.set_title(f"{title} (n={n_docs})", fontsize=13, fontweight="bold")
        ax.grid(True, which="major", axis="both", alpha=0.20, linewidth=0.6)
        ax.tick_params(labelsize=11)
        ax.set_ylim(*ylim)
        ax.set_xlim(*xlim)

    handles = [
        Line2D([], [], marker="o", color="w", markerfacecolor="0.5",
               markeredgecolor="black", markersize=9, label="VLM"),
        Line2D([], [], marker="s", color="w", markerfacecolor="0.5",
               markeredgecolor="black", markersize=9, label="OCR engine"),
        Line2D([], [], linestyle="--", color="0.55", lw=1.4, label="Pareto frontier"),
    ]
    axes[0].legend(handles=handles, loc="lower right", fontsize=9.5,
                   frameon=True, framealpha=0.9, handletextpad=0.4, borderpad=0.5)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path
