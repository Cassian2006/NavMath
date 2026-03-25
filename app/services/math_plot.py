from __future__ import annotations

import re
from typing import Any

import numpy as np
import sympy as sp


SAFE_LOCALS = {
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "sqrt": sp.sqrt,
    "exp": sp.exp,
    "log": sp.log,
    "pi": sp.pi,
}

FORMULA_PATTERNS = [
    r"z\s*=\s*[-+*/^().,A-Za-z0-9_\s]+",
    r"y\s*=\s*[-+*/^().,A-Za-z0-9_\s]+",
    r"x\s*=\s*[-+*/^().,A-Za-z0-9_\s]+",
]


def _normalize_expression(expression: str) -> str:
    return expression.strip().replace("^", "**")


def extract_formula_text(text: str) -> str:
    cleaned = text.strip()
    for pattern in FORMULA_PATTERNS:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            candidate = match.group(0).strip()
            candidate = re.split(r"[\u4e00-\u9fff，。；;！？!?]", candidate)[0].strip()
            return candidate
    return cleaned


def infer_plot_type(formula: str) -> str:
    compact = extract_formula_text(formula).replace(" ", "").lower()
    if compact.startswith("z="):
        return "surface"
    if compact.startswith(("y=", "x=", "r=")):
        return "curve"
    if "x" in compact and "y" in compact:
        return "surface"
    return "curve"


def extract_expression(formula: str) -> tuple[str, str]:
    cleaned = _normalize_expression(extract_formula_text(formula))
    match = re.match(r"^\s*([xyzr])\s*=\s*(.+)$", cleaned, flags=re.IGNORECASE)
    if match:
        return match.group(1).lower(), match.group(2).strip()
    return "y", cleaned


def build_plot_bundle(formula: str) -> dict[str, Any]:
    normalized_formula = extract_formula_text(formula)
    spec = build_plot_spec(normalized_formula)
    spec["matlab_code"] = generate_matlab_code(normalized_formula, spec["plot_type"])
    spec["teaching_tip"] = generate_teaching_tip(normalized_formula, spec["plot_type"])
    spec["plot_label"] = "三维曲面" if spec["plot_type"] == "surface" else "二维函数"
    return spec


def build_plot_spec(formula: str) -> dict[str, Any]:
    if infer_plot_type(formula) == "surface":
        return build_surface_plot(formula)
    return build_curve_plot(formula)


def build_curve_plot(formula: str) -> dict[str, Any]:
    left, expression = extract_expression(formula)
    x = sp.symbols("x")
    expr = sp.sympify(expression, locals=SAFE_LOCALS)
    func = sp.lambdify(x, expr, modules=["numpy"])

    x_values = np.linspace(-6, 6, 240)
    y_values = np.real_if_close(func(x_values)).astype(float)

    return {
        "plot_type": "curve",
        "data": [
            {
                "type": "scatter",
                "mode": "lines",
                "x": x_values.round(4).tolist(),
                "y": y_values.round(4).tolist(),
                "line": {"color": "#0f766e", "width": 3},
                "name": left,
            }
        ],
        "layout": {
            "title": f"二维函数图像：{extract_formula_text(formula)}",
            "paper_bgcolor": "#ffffff",
            "plot_bgcolor": "#f8fafc",
            "margin": {"l": 40, "r": 20, "t": 56, "b": 40},
            "xaxis": {"title": "x", "gridcolor": "#cbd5e1"},
            "yaxis": {"title": left, "gridcolor": "#cbd5e1"},
        },
        "summary": "已生成二维函数图像，可用于观察函数的单调性、零点和周期性等特征。",
    }


def build_surface_plot(formula: str) -> dict[str, Any]:
    _, expression = extract_expression(formula)
    x, y = sp.symbols("x y")
    expr = sp.sympify(expression, locals=SAFE_LOCALS)
    func = sp.lambdify((x, y), expr, modules=["numpy"])

    axis_values = np.linspace(-4, 4, 70)
    x_grid, y_grid = np.meshgrid(axis_values, axis_values)
    z_grid = np.real_if_close(func(x_grid, y_grid)).astype(float)
    z_grid = np.nan_to_num(z_grid, nan=0.0, posinf=10.0, neginf=-10.0)
    z_grid = np.clip(z_grid, -10.0, 10.0)

    return {
        "plot_type": "surface",
        "data": [
            {
                "type": "surface",
                "x": x_grid.round(4).tolist(),
                "y": y_grid.round(4).tolist(),
                "z": z_grid.round(4).tolist(),
                "colorscale": [
                    [0.0, "#0f766e"],
                    [0.5, "#f8fafc"],
                    [1.0, "#ea580c"],
                ],
            }
        ],
        "layout": {
            "title": f"三维曲面图像：{extract_formula_text(formula)}",
            "paper_bgcolor": "#ffffff",
            "margin": {"l": 0, "r": 0, "t": 56, "b": 0},
            "scene": {
                "xaxis": {"title": "x", "backgroundcolor": "#f8fafc"},
                "yaxis": {"title": "y", "backgroundcolor": "#f8fafc"},
                "zaxis": {"title": "z", "backgroundcolor": "#f8fafc"},
                "camera": {"eye": {"x": 1.45, "y": 1.45, "z": 0.9}},
            },
        },
        "summary": "已生成三维曲面图像，可旋转观察曲面的开口方向、鞍点和截面特征。",
    }


def suggest_formula(text: str) -> str | None:
    for pattern in FORMULA_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return extract_formula_text(match.group(0))
    return None


def generate_matlab_code(formula: str, plot_type: str) -> str:
    normalized_formula = extract_formula_text(formula)
    left, expression = extract_expression(normalized_formula)
    matlab_expression = expression.replace("**", ".^")

    if plot_type == "surface":
        return "\n".join(
            [
                "[x, y] = meshgrid(-4:0.1:4, -4:0.1:4);",
                f"z = {matlab_expression};",
                "surf(x, y, z);",
                "shading interp;",
                "xlabel('x'); ylabel('y'); zlabel('z');",
                f"title('{normalized_formula}');",
                "grid on; rotate3d on;",
            ]
        )

    return "\n".join(
        [
            "x = -6:0.05:6;",
            f"{left} = {matlab_expression};",
            f"plot(x, {left}, 'LineWidth', 2);",
            "xlabel('x'); ylabel('y');",
            f"title('{normalized_formula}');",
            "grid on;",
        ]
    )


def generate_teaching_tip(formula: str, plot_type: str) -> str:
    normalized_formula = extract_formula_text(formula)
    if plot_type == "surface":
        return f"该公式适合做三维演示，可结合主截面、等高线和旋转视角解释 {normalized_formula} 的空间形状。"
    return f"该公式适合做二维函数演示，可结合零点、极值和周期性说明 {normalized_formula} 的变化规律。"
