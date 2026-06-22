"""Regenerate ``fig_frontier``: field-value recall against processing time.

Two panels, Brazilian forms (left) and identity documents (right). Marker shape
encodes engine type (VLM / classical / specialized); the dashed line traces the
Pareto frontier (lowest latency at or above each recall level). The figure is
derived entirely from the consolidated results, so it tracks the numbers the
paper reports. Matplotlib is an optional dependency, pulled in only by the
``[figure]`` extra.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import ENGINE_BY_KEY

_MARKER = {"vlm": "o", "classical": "s", "specialized": "^"}
_PANELS = (("forms", "Brazilian forms"), ("ids", "Identity documents"))


def _points(results: dict[str, dict[str, Any]], axis: str) -> list[tuple[float, float, str, str]]:
    """(latency, fvr, type, display) for engines with both on this axis."""
    lat_key = "forms_med" if axis == "forms" else "ids_med"
    pts = []
    for key, r in results.items():
        block = r.get(axis)
        lat = (r.get("latency") or {}).get(lat_key)
        if not block or block.get("fvr") is None or lat is None:
            continue
        pts.append((lat, block["fvr"], r["type"], ENGINE_BY_KEY[key].display))
    return pts


def _pareto(points: list[tuple[float, float, str, str]]) -> list[tuple[float, float]]:
    """Frontier maximizing recall while minimizing latency (lower-left optimal)."""
    best: list[tuple[float, float]] = []
    for lat, fvr, *_ in sorted(points):
        while best and best[-1][1] <= fvr:
            best.pop()
        if not best or fvr > best[-1][1]:
            best.append((lat, fvr))
    return best


def render(results: dict[str, dict[str, Any]], out_path: Path) -> Path:
    """Write ``fig_frontier`` (PDF) and return its path."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, (axis, title) in zip(axes, _PANELS, strict=True):
        pts = _points(results, axis)
        for lat, fvr, etype, name in pts:
            ax.scatter(lat, fvr, marker=_MARKER.get(etype, "o"), s=60,
                       edgecolor="black", linewidth=0.5, zorder=3)
            ax.annotate(name, (lat, fvr), fontsize=6,
                        xytext=(3, 3), textcoords="offset points")
        front = _pareto(pts)
        if len(front) >= 2:
            ax.plot([p[0] for p in front], [p[1] for p in front],
                    "k--", linewidth=1, zorder=2)
        ax.set_title(title)
        ax.set_xlabel("Median processing time (s/page)")
        ax.set_ylabel("Field-value recall")
        ax.grid(True, linewidth=0.3, alpha=0.5)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return out_path
