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
    ("z = x^2 + y^2", "z = x + y"),
    ("z = x^2 - y^2", "z = x - y"),
    ("z = x*y", "z = x + y"),
    ("z = sin(x) + cos(y)", "z = x/2 + y/3"),
    ("z = exp(-(x^2 + y^2))", "z = x - y"),
    ("z = sqrt(x^2 + y^2)", "z = x/2"),
    ("z = ln(x^2 + y^2 + 1)", "z = y/2"),
    ("z = sin(x*y)", "z = x - y/2"),
    ("z = cos(x)*sin(y)", "z = x/3 + y/3"),
    ("z = x^3 - y^2", "z = x + 1"),
    ("z = x^2 + y^2", "z = 2 - x^2 - y^2"),
    ("z = x^2 - y^2", "z = y^2 - x^2"),
    ("z = sin(x) + cos(y)", "z = cos(x) + sin(y)"),
    ("z = x*y", "z = -x*y"),
    ("z = exp(-(x^2 + y^2))", "z = 0.5*exp(-((x-1)^2 + (y-1)^2))"),
    ("z = sqrt(x^2 + y^2)", "z = 2 - sqrt(x^2 + y^2)"),
    ("z = ln(x^2 + y^2 + 1)", "z = 2 - ln(x^2 + y^2 + 1)"),
    ("z = sin(sqrt(x^2 + y^2))", "z = cos(sqrt(x^2 + y^2))"),
    ("z = x^2 + y^2", "z = x^2 - y^2 + 1"),
    ("z = sin(x)*cos(y)", "z = cos(x)*sin(y)"),
    ("z = x^3 + y^3", "z = x^2 - y^2"),
    ("z = x^2*y", "z = x*y^2"),
    ("z = sin(x+y)", "z = cos(x-y)"),
    ("z = exp(-x^2) + exp(-y^2)", "z = exp(-(x^2 + y^2))"),
    ("z = x^2 + y^2", "z = sqrt(x^2 + y^2)"),
    ("z = sin(x^2 + y^2)", "z = cos(x^2 + y^2)"),
    ("z = x/(1+x^2+y^2)", "z = y/(1+x^2+y^2)"),
    ("z = x^2 - y^2", "z = x*y"),
    ("z = sin(x)*sin(y)", "z = cos(x)*cos(y)"),
    ("z = ln(x^2 + y^2 + 1)", "z = sqrt(x^2 + y^2)"),
]

CLIENT = TestClient(app)
OUTPUT_DIR = ROOT / "artifacts" / "surface_pipeline_catalog"


def _fetch_pipeline_pair(left: str, right: str) -> dict:
    query = f"请在同一张图上画 {left} 和 {right}"
    response = CLIENT.post("/api/analyze-text", data={"question_text": query})
    response.raise_for_status()
    body = response.json()
    return body["plot"]


def _render_surface_pair(ax, pair_index: int, left: str, right: str, plot: dict) -> None:
    surfaces = [trace for trace in plot.get("data", []) if trace.get("type") == "surface"]
    for idx, trace in enumerate(surfaces[:2]):
        x = np.asarray(trace.get("x", []), dtype=float)
        y = np.asarray(trace.get("y", []), dtype=float)
        z = np.asarray(trace.get("z", []), dtype=float)
        cmap = "viridis" if idx == 0 else "plasma"
        alpha = 0.84 if idx == 0 else 0.68
        ax.plot_surface(x, y, z, cmap=cmap, linewidth=0, antialiased=True, alpha=alpha)
    ax.view_init(elev=28, azim=-58)
    ax.set_xlabel("x", fontsize=8)
    ax.set_ylabel("y", fontsize=8)
    ax.set_zlabel("z", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.set_title(f"{pair_index:02d}. {left}  +  {right}", fontsize=10, pad=10)


def export_pipeline_pages(per_page: int = 4) -> tuple[list[Path], Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pages: list[Path] = []
    records: list[dict] = []
    total_pages = ceil(len(PAIR_CASES) / per_page)

    for page_index in range(total_pages):
        chunk = PAIR_CASES[page_index * per_page : (page_index + 1) * per_page]
        fig = plt.figure(figsize=(18, 18), constrained_layout=True)
        subfigs = fig.subfigures(2, 2)
        flat_subfigs = [subfigs[r][c] for r in range(2) for c in range(2)]

        for local_index, (left, right) in enumerate(chunk):
            plot = _fetch_pipeline_pair(left, right)
            records.append(
                {
                    "pair_index": page_index * per_page + local_index + 1,
                    "left": left,
                    "right": right,
                    "plot_type": plot.get("plot_type"),
                    "expression_type": plot.get("expression_type"),
                    "trace_count": len(plot.get("data", [])),
                    "matlab_ok": bool(plot.get("matlab_code", "").strip()),
                    "summary": plot.get("summary"),
                }
            )
            ax = flat_subfigs[local_index].add_subplot(111, projection="3d")
            _render_surface_pair(ax, page_index * per_page + local_index + 1, left, right, plot)

        for empty_index in range(len(chunk), len(flat_subfigs)):
            flat_subfigs[empty_index].add_subplot(111).axis("off")

        fig.suptitle(f"NavMath Vision Surface Pipeline Catalog / Page {page_index + 1}", fontsize=18, y=0.995)
        output_path = OUTPUT_DIR / f"surface_pipeline_page_{page_index + 1}.png"
        fig.savefig(output_path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        pages.append(output_path)

    report_path = OUTPUT_DIR / "surface_pipeline_report.json"
    report_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return pages, report_path


if __name__ == "__main__":
    pages, report = export_pipeline_pages()
    for path in pages:
        print(path.resolve())
    print(report.resolve())
