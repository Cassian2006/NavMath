from __future__ import annotations

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

OUTPUT = ROOT / "artifacts" / "matlab_export_examples.png"
CLIENT = TestClient(app)


EXAMPLES = [
    {
        "input": "y = x^2 - 2x + 1",
        "title": "Quadratic Function",
        "code": "x = -6:0.05:6;\ny = x.^2 - 2*x + 1;\nplot(x, y, 'LineWidth', 2);\nxlabel('x'); ylabel('y');\ngrid on;",
    },
    {
        "input": "z = x^2 - y^2",
        "title": "Saddle Surface",
        "code": "[x, y] = meshgrid(-4:0.1:4, -4:0.1:4);\nz = x.^2 - y.^2;\nsurf(x, y, z);\nxlabel('x'); ylabel('y'); zlabel('z');\ngrid on; rotate3d on;",
    },
    {
        "input": "x = cos(t), y = sin(t)",
        "title": "Parametric Circle",
        "code": "t = 0:0.02:2*pi;\nx = cos(t);\ny = sin(t);\nplot(x, y, 'LineWidth', 2);\nxlabel('x'); ylabel('y');\naxis equal; grid on;",
    },
    {
        "input": "r = 1 + 2*cos(theta)",
        "title": "Polar Limacon",
        "code": "theta = 0:0.02:2*pi;\nr = 1 + 2*cos(theta);\npolarplot(theta, r, 'LineWidth', 2);\ngrid on;",
    },
]


def style_box(ax, face="#f8fafc", edge="#d7e0ea") -> None:
    ax.set_facecolor(face)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor(edge)
        spine.set_linewidth(1.2)


def draw_input(ax, example: dict) -> None:
    ax.axis("off")
    style_box(ax, face="#f5f9fc")
    ax.text(0.05, 0.87, "Input", fontsize=18, fontweight="bold", color="#0f172a")
    ax.text(0.05, 0.58, example["input"], fontsize=27, fontweight="bold", color="#0f766e")
    ax.text(0.05, 0.2, example["title"], fontsize=15, color="#475569")


def draw_code(ax, example: dict) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("#0f172a")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, facecolor="#0f172a", edgecolor="#1e293b", linewidth=1.2))
    ax.text(0.05, 0.93, "MATLAB Code", fontsize=18, fontweight="bold", color="#f8fafc")
    ax.text(
        0.05,
        0.84,
        example["code"],
        fontsize=14.2,
        color="#e2e8f0",
        family="monospace",
        va="top",
        linespacing=1.52,
    )


def fetch_plot_bundle(formula: str) -> dict:
    response = CLIENT.post("/api/analyze-text", data={"question_text": f"请画 {formula}"})
    response.raise_for_status()
    return response.json()["plot"]


def draw_plot(ax, example: dict, plot: dict) -> None:
    style_box(ax, face="#ffffff")
    dimension = plot.get("dimension", "2d")
    trace = (plot.get("data") or [{}])[0]

    if dimension == "3d":
        x = np.asarray(trace.get("x", []), dtype=float)
        y = np.asarray(trace.get("y", []), dtype=float)
        z = np.asarray(trace.get("z", []), dtype=float)
        if x.ndim == 2 and y.ndim == 2 and z.ndim == 2:
            ax.plot_surface(x, y, z, cmap="viridis", linewidth=0, antialiased=True, alpha=0.95)
        else:
            ax.plot(x, y, z, color="#0f766e", linewidth=2.4)
        ax.set_xlabel("x", fontsize=10)
        ax.set_ylabel("y", fontsize=10)
        ax.set_zlabel("z", fontsize=10)
        ax.view_init(elev=28, azim=-58)
    elif trace.get("type") == "contour":
        x = np.asarray(trace.get("x", []), dtype=float)
        y = np.asarray(trace.get("y", []), dtype=float)
        z = np.asarray(trace.get("z", []), dtype=float)
        xx, yy = np.meshgrid(x, y)
        ax.contour(xx, yy, z, levels=[0], colors=["#0f766e"], linewidths=2.0)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("x", fontsize=11)
        ax.set_ylabel("y", fontsize=11)
        ax.grid(True, alpha=0.22)
    else:
        x = np.asarray(trace.get("x", []), dtype=float)
        y = np.asarray(trace.get("y", []), dtype=float)
        ax.plot(x, y, color="#0f766e", linewidth=2.4)
        if plot.get("expression_type") in {"parametric2d", "polar2d"}:
            ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("x", fontsize=11)
        ax.set_ylabel("y", fontsize=11)
        ax.grid(True, alpha=0.22)
    ax.set_title("Plot", fontsize=18, fontweight="bold", color="#0f172a", pad=14)
    ax.tick_params(labelsize=10)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(19, 21), facecolor="#eef4f7", constrained_layout=True)
    subfigs = fig.subfigures(4, 3, wspace=0.03, hspace=0.045)

    for row, example in enumerate(EXAMPLES):
        plot = fetch_plot_bundle(example["input"])
        input_ax = subfigs[row][0].add_subplot(111)
        draw_input(input_ax, example)

        plot_ax = subfigs[row][1].add_subplot(111, projection="3d" if plot.get("dimension") == "3d" else None)
        draw_plot(plot_ax, example, plot)

        code_ax = subfigs[row][2].add_subplot(111)
        draw_code(code_ax, example)

    fig.suptitle("MATLAB Intelligent Plot Export Examples", fontsize=32, fontweight="bold", color="#0f172a")
    fig.savefig(OUTPUT, dpi=220, bbox_inches="tight")
    print(OUTPUT.resolve())


if __name__ == "__main__":
    main()
