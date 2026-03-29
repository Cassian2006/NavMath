from __future__ import annotations

import json
import sys
from math import ceil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app


PAIR_CASES = [
    ("y = x", "y = x^2"),
    ("y = x^2", "y = 2 - x^2"),
    ("y = sin(x)", "y = 0"),
    ("y = cos(x)", "y = x"),
    ("y = e^x", "y = 2"),
    ("y = ln(x)", "y = 0"),
    ("y = abs(x)", "y = 1"),
    ("y = x^3", "y = x"),
    ("y = 1/x", "y = x"),
    ("y = x^2 - 1", "y = 0"),
    ("x^2 + y^2 = 1", "y = x"),
    ("x^2 + y^2 = 4", "y = 1"),
    ("x^2/4 + y^2 = 1", "y = x/2"),
    ("x^2 - y^2 = 1", "y = x - 1"),
    ("xy = 1", "y = x"),
    ("x = cos(t), y = sin(t)", "y = 0.5"),
    ("x = t, y = t^2", "y = 2x + 1"),
    ("x = cos(t)^3, y = sin(t)^3", "y = x"),
    ("z = x^2 + y^2", "z = 2"),
    ("z = x^2 - y^2", "z = 1"),
]

CLIENT = TestClient(app)
OUTPUT_DIR = ROOT / "artifacts" / "overlay_catalog"


def _fetch_plot(formula: str) -> dict:
    response = CLIENT.post("/api/analyze-text", data={"question_text": f"请画 {formula}"})
    response.raise_for_status()
    body = response.json()
    plot = body["plot"]
    return {
      "formula": formula,
      "plot_type": plot.get("plot_type"),
      "expression_type": plot.get("expression_type"),
      "matlab_ok": bool(plot.get("matlab_code", "").strip()),
      "plot": plot,
    }


def _plot_trace_2d(ax, trace: dict, color: str) -> None:
    trace_type = trace.get("type")
    if trace_type == "contour":
        x = np.asarray(trace.get("x", []), dtype=float)
        y = np.asarray(trace.get("y", []), dtype=float)
        z = np.asarray(trace.get("z", []), dtype=float)
        xx, yy = np.meshgrid(x, y)
        ax.contour(xx, yy, z, levels=[0], colors=[color], linewidths=1.8)
        ax.set_aspect("equal", adjustable="box")
        return

    x = np.asarray(trace.get("x", []), dtype=float)
    y = np.asarray(trace.get("y", []), dtype=float)
    if x.size and y.size:
        ax.plot(x, y, color=color, linewidth=1.8)


def _plot_trace_3d(ax, trace: dict, cmap: str) -> None:
    x = np.asarray(trace.get("x", []), dtype=float)
    y = np.asarray(trace.get("y", []), dtype=float)
    z = np.asarray(trace.get("z", []), dtype=float)
    if x.ndim == 2 and y.ndim == 2 and z.ndim == 2:
        ax.plot_surface(x, y, z, cmap=cmap, linewidth=0, antialiased=True, alpha=0.78)
    else:
        ax.plot(x, y, z, linewidth=1.8)
    ax.view_init(elev=28, azim=-58)


def _render_pair(ax, pair_index: int, left: dict, right: dict) -> None:
    left_plot = left["plot"]
    right_plot = right["plot"]
    dimension = left_plot.get("dimension", "2d")

    if dimension == "3d":
        _plot_trace_3d(ax, left_plot["data"][0], "viridis")
        _plot_trace_3d(ax, right_plot["data"][0], "plasma")
        ax.set_xlabel("x", fontsize=8)
        ax.set_ylabel("y", fontsize=8)
        ax.set_zlabel("z", fontsize=8)
    else:
        _plot_trace_2d(ax, left_plot["data"][0], "#0f766e")
        _plot_trace_2d(ax, right_plot["data"][0], "#ea580c")
        ax.grid(True, alpha=0.22)
        ax.set_xlabel("x", fontsize=8)
        ax.set_ylabel("y", fontsize=8)

    ax.tick_params(labelsize=7)
    ax.set_title(f"{pair_index:02d}. {left['formula']}  +  {right['formula']}", fontsize=10, pad=10)


def export_overlay_pages(per_page: int = 4) -> tuple[list[Path], Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pages: list[Path] = []
    records: list[dict] = []
    total_pages = ceil(len(PAIR_CASES) / per_page)

    for page_index in range(total_pages):
        chunk = PAIR_CASES[page_index * per_page : (page_index + 1) * per_page]
        fig = plt.figure(figsize=(18, 18), constrained_layout=True)
        subfigs = fig.subfigures(2, 2)
        flat_subfigs = [subfigs[r][c] for r in range(2) for c in range(2)]

        for local_index, pair in enumerate(chunk):
            left = _fetch_plot(pair[0])
            right = _fetch_plot(pair[1])
            records.append(
                {
                    "pair_index": page_index * per_page + local_index + 1,
                    "left": {
                        "formula": left["formula"],
                        "plot_type": left["plot_type"],
                        "expression_type": left["expression_type"],
                        "matlab_ok": left["matlab_ok"],
                    },
                    "right": {
                        "formula": right["formula"],
                        "plot_type": right["plot_type"],
                        "expression_type": right["expression_type"],
                        "matlab_ok": right["matlab_ok"],
                    },
                }
            )
            dimension = left["plot"].get("dimension", "2d")
            ax = flat_subfigs[local_index].add_subplot(111, projection="3d" if dimension == "3d" else None)
            _render_pair(ax, page_index * per_page + local_index + 1, left, right)

        for empty_index in range(len(chunk), len(flat_subfigs)):
            flat_subfigs[empty_index].add_subplot(111).axis("off")

        fig.suptitle(f"NavMath Vision Overlay Catalog / Page {page_index + 1}", fontsize=18, y=0.995)
        output_path = OUTPUT_DIR / f"overlay_catalog_page_{page_index + 1}.png"
        fig.savefig(output_path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        pages.append(output_path)

    report_path = OUTPUT_DIR / "overlay_catalog_report.json"
    report_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return pages, report_path


if __name__ == "__main__":
    pages, report = export_overlay_pages()
    for path in pages:
        print(path.resolve())
    print(report.resolve())
