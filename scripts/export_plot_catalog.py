from __future__ import annotations

from math import ceil
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app


PLOT_CASES = [
    "y = x",
    "y = x^2",
    "y = x^3 - 3x",
    "y = 1/x",
    "y = sqrt(x)",
    "y = abs(x)",
    "y = sin(x)",
    "y = cos(x)",
    "y = tan(x)",
    "y = e^x",
    "y = ln(x)",
    "y = x*sin(x)",
    "y = sin(1/x)",
    "y = x/(1+x^2)",
    "y = floor(x)",
    "z = x + y",
    "z = x^2 + y^2",
    "z = x^2 - y^2",
    "z = sin(x)*cos(y)",
    "z = exp(-(x^2 + y^2))",
    "z = sqrt(x^2 + y^2)",
    "z = ln(x^2 + y^2 + 1)",
    "z = x*y",
    "z = sin(sqrt(x^2 + y^2))",
    "z = 1/(1 + x^2 + y^2)",
    "x = t, y = t^2",
    "x = cos(t), y = sin(t)",
    "x = 2*cos(t), y = sin(t)",
    "x = cos(2t), y = sin(3t)",
    "x = t*cos(t), y = t*sin(t)",
    "x = sin(t), y = t",
    "x = t - sin(t), y = 1 - cos(t)",
    "x = cos(t)^3, y = sin(t)^3",
    "x = (1+0.5*cos(8t))*cos(t), y = (1+0.5*cos(8t))*sin(t)",
    "x = sin(3t), y = sin(4t)",
    "r = 1",
    "r = 2*cos(theta)",
    "r = 2*sin(theta)",
    "r = 1 + cos(theta)",
    "r = 1 + 2*sin(theta)",
    "r = cos(4theta)",
    "r = theta",
    "x^2 + y^2 = 1",
    "x^2/4 + y^2 = 1",
    "x^2 - y^2 = 1",
    "xy = 1",
    "x^3 - y^2 = 0",
    "x^(2/3) + y^(2/3) = 1",
    "sin(x) + cos(y) = 0",
    "x^4 + y^4 = 1",
]

CLIENT = TestClient(app)
OUTPUT_DIR = ROOT / "artifacts" / "plot_catalog"


def _fetch_plot(formula: str) -> dict:
    response = CLIENT.post("/api/analyze-text", data={"question_text": f"请画 {formula}"})
    response.raise_for_status()
    body = response.json()
    return body["plot"]


def _plot_2d(ax, trace: dict) -> None:
    x = np.asarray(trace.get("x", []), dtype=float)
    y = np.asarray(trace.get("y", []), dtype=float)
    if trace.get("type") == "contour":
        z = np.asarray(trace.get("z", []), dtype=float)
        xx, yy = np.meshgrid(x, y)
        ax.contour(xx, yy, z, levels=[0], colors="#0f766e", linewidths=1.6)
        ax.set_aspect("equal", adjustable="box")
        return

    if x.size and y.size:
        ax.plot(x, y, color="#0f766e", linewidth=1.8)
        finite_x = x[np.isfinite(x)]
        finite_y = y[np.isfinite(y)]
        if finite_x.size and finite_y.size:
            ax.set_xlim(np.nanmin(finite_x), np.nanmax(finite_x))
            ax.set_ylim(np.nanmin(finite_y), np.nanmax(finite_y))


def _plot_3d(ax, trace: dict) -> None:
    x = np.asarray(trace.get("x", []), dtype=float)
    y = np.asarray(trace.get("y", []), dtype=float)
    z = np.asarray(trace.get("z", []), dtype=float)
    if x.ndim == 2 and y.ndim == 2 and z.ndim == 2:
        ax.plot_surface(x, y, z, cmap="viridis", linewidth=0, antialiased=True)
    else:
        ax.plot(x, y, z, color="#0f766e", linewidth=1.8)
    ax.view_init(elev=28, azim=-58)


def _render_case(ax, formula: str, plot: dict, index: int) -> None:
    data = plot.get("data", [])
    dimension = plot.get("dimension", "2d")
    if not data:
        ax.text(0.5, 0.5, "No plot", ha="center", va="center")
        ax.axis("off")
        return

    if dimension == "3d":
        _plot_3d(ax, data[0])
        ax.set_xlabel("x", fontsize=8)
        ax.set_ylabel("y", fontsize=8)
        ax.set_zlabel("z", fontsize=8)
    else:
        _plot_2d(ax, data[0])
        ax.set_xlabel("x", fontsize=8)
        ax.set_ylabel("y", fontsize=8)
        ax.grid(True, alpha=0.2)

    ax.tick_params(labelsize=7)
    ax.set_title(f"{index:02d}. {formula}", fontsize=10, pad=10)


def export_pages(chunk_size: int = 10) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pages: list[Path] = []
    total_pages = ceil(len(PLOT_CASES) / chunk_size)

    for page_index in range(total_pages):
        chunk = PLOT_CASES[page_index * chunk_size : (page_index + 1) * chunk_size]
        fig = plt.figure(figsize=(18, 24), constrained_layout=True)
        subfigs = fig.subfigures(5, 2)
        flat_subfigs = [subfigs[r][c] for r in range(5) for c in range(2)]

        for local_index, formula in enumerate(chunk):
            plot = _fetch_plot(formula)
            subfig = flat_subfigs[local_index]
            dimension = plot.get("dimension", "2d")
            ax = subfig.add_subplot(111, projection="3d" if dimension == "3d" else None)
            _render_case(ax, formula, plot, page_index * chunk_size + local_index + 1)

        for empty_index in range(len(chunk), len(flat_subfigs)):
            flat_subfigs[empty_index].add_subplot(111).axis("off")

        fig.suptitle(f"NavMath Vision Plot Catalog / Page {page_index + 1}", fontsize=18, y=0.995)
        output_path = OUTPUT_DIR / f"plot_catalog_page_{page_index + 1}.png"
        fig.savefig(output_path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        pages.append(output_path)

    return pages


if __name__ == "__main__":
    generated = export_pages()
    for path in generated:
        print(path.resolve())
