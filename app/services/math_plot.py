from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


SAFE_LOCALS = {
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "sqrt": sp.sqrt,
    "exp": sp.exp,
    "log": sp.log,
    "ln": sp.log,
    "abs": sp.Abs,
    "floor": sp.floor,
    "pi": sp.pi,
    "e": sp.E,
}

PARSE_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

FORMULA_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])([xyzr])\s*=\s*(.*?)(?=(?:(?<![A-Za-z0-9_])[xyzr]\s*=)|(?:\s+and\s+)|(?:\s+with\s+)|$|[，。；;！？!\n])",
    flags=re.IGNORECASE,
)
RANGE_PATTERN = re.compile(
    r"([a-zA-Z][a-zA-Z0-9_]*)\s*(?:∈|in)\s*\[\s*([^,\]]+)\s*,\s*([^\]]+)\s*\]",
    flags=re.IGNORECASE,
)
EDIT_KEYWORDS = ("保留", "裁剪", "只看", "只显示", "只保留", "截取", "去掉")

CURVE_COLORS = ["#0f766e", "#ea580c", "#2563eb", "#9333ea"]
SURFACE_COLORS = [
    [[0.0, "#0f766e"], [0.5, "#99f6e4"], [1.0, "#14b8a6"]],
    [[0.0, "#7c3aed"], [0.5, "#ddd6fe"], [1.0, "#c084fc"]],
]


@dataclass
class TraceSpec:
    kind: str
    name: str
    x: list[float] | None = None
    y: list[float] | None = None
    z: list[float] | list[list[float]] | None = None
    mode: str | None = None
    line: dict[str, Any] | None = None
    marker: dict[str, Any] | None = None
    text: list[str] | None = None
    opacity: float | None = None
    colorscale: Any = None
    showscale: bool | None = None
    showlegend: bool | None = None
    hidesurface: bool | None = None
    contours: dict[str, Any] | None = None
    visible: bool = True


@dataclass
class PlotSpec:
    plot_type: str
    expression_type: str
    dimension: str
    title: str
    summary: str
    axis_titles: dict[str, str]
    variables: list[str]
    formulas: list[str]
    traces: list[TraceSpec] = field(default_factory=list)
    parameter_ranges: dict[str, tuple[float, float]] = field(default_factory=dict)
    annotations: list[dict[str, Any]] = field(default_factory=list)
    matlab_code: str = ""
    teaching_tip: str = ""
    plot_label: str = ""
    parser: str = "local"


def _normalize_expression(expression: str) -> str:
    return expression.strip().replace("^", "**")


def _parse_expression(expression: str, locals_dict: dict[str, Any] | None = None) -> sp.Expr:
    return parse_expr(
        _normalize_expression(expression),
        local_dict=locals_dict or SAFE_LOCALS,
        transformations=PARSE_TRANSFORMATIONS,
        evaluate=True,
    )


def normalize_formula_text(formula: str) -> str:
    cleaned = str(formula or "").strip().replace("**", "^")
    match = re.match(r"^\s*([xyzr])\s*=\s*(.+)$", cleaned, flags=re.IGNORECASE)
    if not match:
        return cleaned
    left, expression = match.group(1).lower(), match.group(2).strip()
    return f"{left} = {expression}"


def extract_expression(formula: str) -> tuple[str, str]:
    cleaned = _normalize_expression(formula)
    match = re.match(r"^\s*([xyzr])\s*=\s*(.+)$", cleaned, flags=re.IGNORECASE)
    if match:
        return match.group(1).lower(), match.group(2).strip()
    return "y", cleaned.strip()


def extract_formula_text(text: str) -> str:
    formulas = extract_formula_texts(text)
    return formulas[0] if formulas else text.strip()


def extract_formula_texts(text: str) -> list[str]:
    formulas: list[str] = []
    for match in FORMULA_PATTERN.finditer(text or ""):
        left = match.group(1).lower()
        expression = match.group(2).strip()
        expression_match = re.match(r"[-+*/^().,A-Za-z0-9_\s]+", expression)
        if not expression_match:
            continue
        expression = expression_match.group(0).strip()
        expression = expression.split(",")[0].strip()
        expression = expression.rstrip(",，；;")
        formula = normalize_formula_text(f"{left} = {expression}")
        if formula not in formulas:
            formulas.append(formula)
    return formulas


def suggest_formula(text: str) -> str | None:
    formulas = extract_formula_texts(text)
    return formulas[0] if formulas else None


def parse_parameter_ranges(text: str) -> dict[str, tuple[float, float]]:
    ranges: dict[str, tuple[float, float]] = {}
    for match in RANGE_PATTERN.finditer(text or ""):
        symbol = match.group(1)
        start = float(sp.N(_parse_expression(match.group(2), SAFE_LOCALS)))
        end = float(sp.N(_parse_expression(match.group(3), SAFE_LOCALS)))
        ranges[symbol] = (start, end)
    return ranges


def parse_axis_filters(text: str) -> dict[str, tuple[float, float] | None]:
    normalized = (text or "").replace(" ", "")
    filters: dict[str, tuple[float, float] | None] = {}
    axis_aliases = {"x": ["x", "横轴"], "y": ["y", "纵轴"], "z": ["z"]}
    for axis, aliases in axis_aliases.items():
        if any(f"{alias}正半轴" in normalized or f"{alias}>0" in normalized for alias in aliases):
            filters[axis] = (0.0, math.inf)
        elif any(f"{alias}负半轴" in normalized or f"{alias}<0" in normalized for alias in aliases):
            filters[axis] = (-math.inf, 0.0)
    return filters


def should_edit_existing_plot(text: str, previous_plot: dict[str, Any] | None) -> bool:
    if not previous_plot:
        return False
    return any(keyword in (text or "") for keyword in EDIT_KEYWORDS) and not extract_formula_texts(text)


def extract_point_annotations(text: str) -> list[dict[str, Any]]:
    if not text or not any(keyword in text for keyword in ("点", "标注", "标记", "经过")):
        return []

    pattern = re.compile(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)(?:\s*,\s*(-?\d+(?:\.\d+)?))?\s*\)")
    annotations: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        x_value = float(match.group(1))
        y_value = float(match.group(2))
        z_group = match.group(3)
        if z_group is None:
            annotations.append({"name": f"({x_value:g}, {y_value:g})", "coords": [x_value, y_value], "dimension": "2d"})
        else:
            annotations.append(
                {
                    "name": f"({x_value:g}, {y_value:g}, {float(z_group):g})",
                    "coords": [x_value, y_value, float(z_group)],
                    "dimension": "3d",
                }
            )
    return annotations


def _safe_numeric(values: Any) -> np.ndarray:
    array = np.asarray(np.real_if_close(values), dtype=np.complex128)
    mask = np.abs(array.imag) < 1e-8
    real = np.where(mask, array.real, np.nan)
    return np.nan_to_num(real, nan=np.nan, posinf=np.nan, neginf=np.nan)


def _broadcast_like(values: Any, template: np.ndarray) -> np.ndarray:
    numeric = _safe_numeric(values)
    if numeric.shape == ():
        fill = float(numeric)
        return np.full_like(template, fill, dtype=float)
    return numeric


def _extract_parameter_symbol(expr: sp.Expr, excluded: set[str] | None = None) -> sp.Symbol | None:
    excluded = excluded or set()
    symbols = sorted((symbol for symbol in expr.free_symbols if str(symbol) not in excluded), key=lambda item: str(item))
    if len(symbols) == 1:
        return symbols[0]
    return None


def _build_plot_type(expression_type: str, trace_count: int) -> str:
    mapping = {
        "explicit2d": "multi_curve" if trace_count > 1 else "curve",
        "parametric2d": "multi_curve" if trace_count > 1 else "curve",
        "explicit3d": "multi_surface" if trace_count > 1 else "surface",
        "parametric3d": "parametric3d",
        "polar2d": "curve",
        "implicit2d": "curve",
    }
    return mapping.get(expression_type, "curve")


def detect_expression_type(formulas: list[str]) -> str:
    normalized = [normalize_formula_text(formula) for formula in formulas if formula.strip()]
    if not normalized:
        return "explicit2d"

    left_sides = [extract_expression(formula)[0] for formula in normalized]
    if set(left_sides) == {"x", "y", "z"} and len(normalized) == 3:
        return "parametric3d"
    if set(left_sides) == {"x", "y"} and len(normalized) == 2:
        return "parametric2d"
    if len(normalized) == 1 and left_sides[0] == "r":
        return "polar2d"
    if all(left == "z" for left in left_sides):
        return "explicit3d"
    if all(left in {"x", "y"} for left in left_sides):
        return "parametric2d" if any(left == "x" for left in left_sides) else "explicit2d"
    return "explicit2d"


def infer_plot_type(formula: str) -> str:
    return infer_plot_type_from_formulas([formula])


def infer_plot_type_from_formulas(formulas: list[str]) -> str:
    expression_type = detect_expression_type(formulas)
    return _build_plot_type(expression_type, len(formulas))


def _extract_implicit_expression(text: str) -> str | None:
    cleaned = (text or "").strip()
    if not cleaned or re.search(r"(?<![A-Za-z0-9_])[xyzr]\s*=", cleaned.lower()):
        return None
    if "=" not in cleaned:
        return None
    candidate = re.sub(r"^.*?(?=[A-Za-z0-9_(\-]*x)", "", cleaned)
    candidate = candidate.strip(" ：:，,。")
    if "x" not in candidate or "y" not in candidate:
        return None
    return candidate


def _trace_to_plotly(trace: TraceSpec) -> dict[str, Any]:
    payload: dict[str, Any] = {"type": trace.kind, "name": trace.name}
    if trace.x is not None:
        payload["x"] = trace.x
    if trace.y is not None:
        payload["y"] = trace.y
    if trace.z is not None:
        payload["z"] = trace.z
    if trace.mode is not None:
        payload["mode"] = trace.mode
    if trace.line is not None:
        payload["line"] = trace.line
    if trace.marker is not None:
        payload["marker"] = trace.marker
    if trace.text is not None:
        payload["text"] = trace.text
    if trace.opacity is not None:
        payload["opacity"] = trace.opacity
    if trace.colorscale is not None:
        payload["colorscale"] = trace.colorscale
    if trace.showscale is not None:
        payload["showscale"] = trace.showscale
    if trace.showlegend is not None:
        payload["showlegend"] = trace.showlegend
    if trace.hidesurface is not None:
        payload["hidesurface"] = trace.hidesurface
    if trace.contours is not None:
        payload["contours"] = trace.contours
    payload["visible"] = trace.visible
    return payload


def _spec_to_layout(spec: PlotSpec) -> dict[str, Any]:
    if spec.dimension == "3d":
        return {
            "title": spec.title,
            "paper_bgcolor": "#ffffff",
            "margin": {"l": 0, "r": 0, "t": 56, "b": 0},
            "scene": {
                "xaxis": {"title": spec.axis_titles.get("x", "x"), "backgroundcolor": "#f8fafc"},
                "yaxis": {"title": spec.axis_titles.get("y", "y"), "backgroundcolor": "#f8fafc"},
                "zaxis": {"title": spec.axis_titles.get("z", "z"), "backgroundcolor": "#f8fafc"},
                "camera": {"eye": {"x": 1.45, "y": 1.45, "z": 0.9}},
            },
            "legend": {"orientation": "h"},
        }

    return {
        "title": spec.title,
        "paper_bgcolor": "#ffffff",
        "plot_bgcolor": "#f8fafc",
        "margin": {"l": 40, "r": 20, "t": 56, "b": 40},
        "xaxis": {"title": spec.axis_titles.get("x", "x"), "gridcolor": "#cbd5e1", "zerolinecolor": "#94a3b8"},
        "yaxis": {"title": spec.axis_titles.get("y", "y"), "gridcolor": "#cbd5e1", "zerolinecolor": "#94a3b8"},
        "legend": {"orientation": "h"},
    }


def _spec_to_bundle(spec: PlotSpec) -> dict[str, Any]:
    plot_spec_payload = asdict(spec)
    plot_spec_payload["traces"] = [asdict(trace) for trace in spec.traces]
    return {
        "plot_type": spec.plot_type,
        "expression_type": spec.expression_type,
        "dimension": spec.dimension,
        "data": [_trace_to_plotly(trace) for trace in spec.traces],
        "layout": _spec_to_layout(spec),
        "summary": spec.summary,
        "matlab_code": spec.matlab_code,
        "teaching_tip": spec.teaching_tip,
        "plot_label": spec.plot_label,
        "formulas": spec.formulas,
        "plot_spec": plot_spec_payload,
    }


def _build_curve_intersections(curves: list[tuple[str, sp.Expr]]) -> TraceSpec | None:
    x = sp.symbols("x")
    points: list[tuple[float, float]] = []
    (formula1, expr1), (formula2, expr2) = curves
    left1, _ = extract_expression(formula1)
    left2, _ = extract_expression(formula2)
    if left1 != "y" or left2 != "y":
        return None

    try:
        solutions = sp.solve(sp.Eq(expr1, expr2), x)
    except Exception:
        solutions = []

    for solution in solutions:
        numeric = sp.N(solution)
        if not numeric.is_real:
            continue
        x_value = float(numeric)
        if not (-6.5 <= x_value <= 6.5):
            continue
        y_value = float(sp.N(expr1.subs(x, solution)))
        if math.isfinite(x_value) and math.isfinite(y_value):
            points.append((x_value, y_value))

    if not points:
        return None

    return TraceSpec(
        kind="scatter",
        name="交点",
        mode="markers+text",
        x=[round(point[0], 4) for point in points],
        y=[round(point[1], 4) for point in points],
        text=["交点"] * len(points),
        marker={"size": 10, "color": "#dc2626", "line": {"width": 1, "color": "#7f1d1d"}},
    )


def _build_surface_intersection(
    surface1: tuple[np.ndarray, np.ndarray, np.ndarray],
    surface2: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> TraceSpec | None:
    x_grid, y_grid, z_grid_1 = surface1
    _, _, z_grid_2 = surface2
    delta = np.abs(z_grid_1 - z_grid_2)
    mask = np.isfinite(delta) & (delta < 0.15)
    if np.count_nonzero(mask) < 10:
        return None

    x_points = x_grid[mask]
    y_points = y_grid[mask]
    z_points = ((z_grid_1 + z_grid_2) / 2)[mask]
    order = np.argsort(x_points)
    return TraceSpec(
        kind="scatter3d",
        name="交线",
        mode="markers+lines",
        x=x_points[order].round(4).tolist(),
        y=y_points[order].round(4).tolist(),
        z=z_points[order].round(4).tolist(),
        marker={"size": 3, "color": "#dc2626"},
        line={"color": "#dc2626", "width": 5},
    )


def _build_explicit_2d_spec(formulas: list[str], parameter_ranges: dict[str, tuple[float, float]]) -> PlotSpec:
    sample_values = np.linspace(-6, 6, 400)
    traces: list[TraceSpec] = []
    symbolic_curves: list[tuple[str, sp.Expr]] = []
    axis_title = "x"
    value_title = "y"
    variables = ["x"]

    for index, formula in enumerate(formulas):
        left, expression = extract_expression(formula)
        expr = _parse_expression(expression, SAFE_LOCALS)
        symbolic_curves.append((formula, expr))

        if left == "y":
            x = sp.symbols("x")
            func = sp.lambdify(x, expr, modules=["numpy"])
            with np.errstate(all="ignore"):
                y_values = _broadcast_like(func(sample_values), sample_values)
            x_values = sample_values
            name = normalize_formula_text(formula)
        else:
            symbol = _extract_parameter_symbol(expr, excluded={left}) or sp.symbols("t")
            domain = parameter_ranges.get(str(symbol), (-6.0, 6.0))
            parameter_samples = np.linspace(domain[0], domain[1], 400)
            func = sp.lambdify(symbol, expr, modules=["numpy"])
            with np.errstate(all="ignore"):
                component_values = _broadcast_like(func(parameter_samples), parameter_samples)
            x_values = parameter_samples
            y_values = component_values
            axis_title = str(symbol)
            value_title = left
            variables = [str(symbol)]
            name = f"{left}({symbol})"

        mask = np.isfinite(x_values) & np.isfinite(y_values)
        traces.append(
            TraceSpec(
                kind="scatter",
                name=name,
                mode="lines",
                x=x_values[mask].round(4).tolist(),
                y=y_values[mask].round(4).tolist(),
                line={"color": CURVE_COLORS[index % len(CURVE_COLORS)], "width": 3},
            )
        )

    if len(symbolic_curves) >= 2:
        intersection_trace = _build_curve_intersections(symbolic_curves[:2])
        if intersection_trace is not None:
            traces.append(intersection_trace)

    title = "、".join(normalize_formula_text(formula) for formula in formulas)
    return PlotSpec(
        plot_type=_build_plot_type("explicit2d", len(formulas)),
        expression_type="explicit2d",
        dimension="2d",
        title=f"二维图像：{title}",
        summary="已生成二维函数图像。" if len(formulas) == 1 else "已生成二维多图层图像，并标出交点。",
        axis_titles={"x": axis_title, "y": value_title},
        variables=variables,
        formulas=formulas,
        traces=traces,
        parameter_ranges=parameter_ranges,
    )


def _build_parametric_2d_spec(formulas: list[str], parameter_ranges: dict[str, tuple[float, float]]) -> PlotSpec:
    expression_map = {extract_expression(formula)[0]: extract_expression(formula)[1] for formula in formulas}
    x_expr = _parse_expression(expression_map["x"], SAFE_LOCALS)
    y_expr = _parse_expression(expression_map["y"], SAFE_LOCALS)
    parameter_symbol = _extract_parameter_symbol(x_expr, excluded={"x"}) or _extract_parameter_symbol(y_expr, excluded={"y"})
    parameter_symbol = parameter_symbol or sp.symbols("t")
    domain = parameter_ranges.get(str(parameter_symbol), (-2 * math.pi, 2 * math.pi))
    samples = np.linspace(domain[0], domain[1], 500)

    x_func = sp.lambdify(parameter_symbol, x_expr, modules=["numpy"])
    y_func = sp.lambdify(parameter_symbol, y_expr, modules=["numpy"])
    with np.errstate(all="ignore"):
        x_values = _broadcast_like(x_func(samples), samples)
        y_values = _broadcast_like(y_func(samples), samples)
    mask = np.isfinite(x_values) & np.isfinite(y_values)

    return PlotSpec(
        plot_type="curve",
        expression_type="parametric2d",
        dimension="2d",
        title="二维参数曲线",
        summary="已生成二维参数曲线。",
        axis_titles={"x": "x", "y": "y"},
        variables=[str(parameter_symbol)],
        formulas=formulas,
        traces=[
            TraceSpec(
                kind="scatter",
                name=f"参数曲线 {parameter_symbol}",
                mode="lines",
                x=x_values[mask].round(4).tolist(),
                y=y_values[mask].round(4).tolist(),
                line={"color": CURVE_COLORS[0], "width": 3},
            )
        ],
        parameter_ranges={str(parameter_symbol): domain},
    )


def _build_explicit_3d_spec(formulas: list[str], parameter_ranges: dict[str, tuple[float, float]]) -> PlotSpec:
    x_range = parameter_ranges.get("x", (-4.0, 4.0))
    y_range = parameter_ranges.get("y", (-4.0, 4.0))
    axis_values_x = np.linspace(x_range[0], x_range[1], 90)
    axis_values_y = np.linspace(y_range[0], y_range[1], 90)
    x_grid, y_grid = np.meshgrid(axis_values_x, axis_values_y)

    traces: list[TraceSpec] = []
    surfaces: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    for index, formula in enumerate(formulas):
        _, expression = extract_expression(formula)
        x, y = sp.symbols("x y")
        expr = _parse_expression(expression, SAFE_LOCALS)
        func = sp.lambdify((x, y), expr, modules=["numpy"])
        with np.errstate(all="ignore"):
            z_grid = np.clip(_broadcast_like(func(x_grid, y_grid), x_grid), -10.0, 10.0)
        surfaces.append((x_grid, y_grid, z_grid))
        traces.append(
            TraceSpec(
                kind="surface",
                name=normalize_formula_text(formula),
                x=x_grid.round(4).tolist(),
                y=y_grid.round(4).tolist(),
                z=np.where(np.isfinite(z_grid), z_grid, np.nan).round(4).tolist(),
                colorscale=SURFACE_COLORS[index % len(SURFACE_COLORS)],
                opacity=(0.92 if index == 0 else 1.0) if len(formulas) > 1 else 0.96,
                showscale=False,
                showlegend=True,
                hidesurface=len(formulas) > 1 and index == 1,
                contours={
                    "x": {"show": len(formulas) > 1 and index == 1, "color": "#6d28d9", "width": 3, "highlight": False},
                    "y": {"show": len(formulas) > 1 and index == 1, "color": "#6d28d9", "width": 3, "highlight": False},
                    "z": {
                        "show": True,
                        "usecolormap": False,
                        "color": "#6d28d9" if index == 1 else "#334155",
                        "width": 3 if index == 1 else 1,
                    },
                },
            )
        )

    if len(surfaces) >= 2:
        intersection_trace = _build_surface_intersection(surfaces[0], surfaces[1])
        if intersection_trace is not None:
            traces.append(intersection_trace)

    title = "、".join(normalize_formula_text(formula) for formula in formulas)
    return PlotSpec(
        plot_type=_build_plot_type("explicit3d", len(formulas)),
        expression_type="explicit3d",
        dimension="3d",
        title=f"三维图像：{title}",
        summary="已生成三维曲面图像。" if len(formulas) == 1 else "已生成三维曲面叠加图像。",
        axis_titles={"x": "x", "y": "y", "z": "z"},
        variables=["x", "y"],
        formulas=formulas,
        traces=traces,
        parameter_ranges=parameter_ranges,
    )


def _build_parametric_3d_spec(formulas: list[str], parameter_ranges: dict[str, tuple[float, float]]) -> PlotSpec:
    expression_map = {extract_expression(formula)[0]: extract_expression(formula)[1] for formula in formulas}
    x_expr = _parse_expression(expression_map["x"], SAFE_LOCALS)
    y_expr = _parse_expression(expression_map["y"], SAFE_LOCALS)
    z_expr = _parse_expression(expression_map["z"], SAFE_LOCALS)
    parameter_symbol = (
        _extract_parameter_symbol(x_expr, excluded={"x"})
        or _extract_parameter_symbol(y_expr, excluded={"y"})
        or _extract_parameter_symbol(z_expr, excluded={"z"})
        or sp.symbols("t")
    )
    domain = parameter_ranges.get(str(parameter_symbol), (-6.0, 6.0))
    samples = np.linspace(domain[0], domain[1], 500)

    x_func = sp.lambdify(parameter_symbol, x_expr, modules=["numpy"])
    y_func = sp.lambdify(parameter_symbol, y_expr, modules=["numpy"])
    z_func = sp.lambdify(parameter_symbol, z_expr, modules=["numpy"])
    with np.errstate(all="ignore"):
        x_values = _broadcast_like(x_func(samples), samples)
        y_values = _broadcast_like(y_func(samples), samples)
        z_values = _broadcast_like(z_func(samples), samples)
    mask = np.isfinite(x_values) & np.isfinite(y_values) & np.isfinite(z_values)

    return PlotSpec(
        plot_type="parametric3d",
        expression_type="parametric3d",
        dimension="3d",
        title="三维参数曲线",
        summary="已生成三维参数曲线。",
        axis_titles={"x": "x", "y": "y", "z": "z"},
        variables=[str(parameter_symbol)],
        formulas=formulas,
        traces=[
            TraceSpec(
                kind="scatter3d",
                name=f"参数曲线 {parameter_symbol}",
                mode="lines",
                x=x_values[mask].round(4).tolist(),
                y=y_values[mask].round(4).tolist(),
                z=z_values[mask].round(4).tolist(),
                line={"color": "#2563eb", "width": 6},
            )
        ],
        parameter_ranges={str(parameter_symbol): domain},
    )


def _build_polar_2d_spec(formulas: list[str], parameter_ranges: dict[str, tuple[float, float]]) -> PlotSpec:
    _, expression = extract_expression(formulas[0])
    theta = sp.symbols("theta")
    expr = _parse_expression(expression, {**SAFE_LOCALS, "theta": theta})
    domain = parameter_ranges.get("theta", (0.0, 2 * math.pi))
    samples = np.linspace(domain[0], domain[1], 500)
    func = sp.lambdify(theta, expr, modules=["numpy"])
    with np.errstate(all="ignore"):
        radius = _broadcast_like(func(samples), samples)
    x_values = radius * np.cos(samples)
    y_values = radius * np.sin(samples)
    mask = np.isfinite(x_values) & np.isfinite(y_values)

    return PlotSpec(
        plot_type="curve",
        expression_type="polar2d",
        dimension="2d",
        title=f"极坐标图像：{normalize_formula_text(formulas[0])}",
        summary="已生成极坐标曲线。",
        axis_titles={"x": "x", "y": "y"},
        variables=["theta"],
        formulas=formulas,
        traces=[
            TraceSpec(
                kind="scatter",
                name="极坐标曲线",
                mode="lines",
                x=x_values[mask].round(4).tolist(),
                y=y_values[mask].round(4).tolist(),
                line={"color": CURVE_COLORS[0], "width": 3},
            )
        ],
        parameter_ranges={"theta": domain},
    )


def _build_implicit_2d_spec(expression: str, parameter_ranges: dict[str, tuple[float, float]]) -> PlotSpec:
    x_range = parameter_ranges.get("x", (-6.0, 6.0))
    y_range = parameter_ranges.get("y", (-6.0, 6.0))
    x_values = np.linspace(x_range[0], x_range[1], 240)
    y_values = np.linspace(y_range[0], y_range[1], 240)
    x_grid, y_grid = np.meshgrid(x_values, y_values)

    if "=" in expression:
        left, right = expression.split("=", 1)
        expr = _parse_expression(left, SAFE_LOCALS) - _parse_expression(right, SAFE_LOCALS)
    else:
        expr = _parse_expression(expression, SAFE_LOCALS)

    x, y = sp.symbols("x y")
    func = sp.lambdify((x, y), expr, modules=["numpy"])
    with np.errstate(all="ignore"):
        z_grid = _safe_numeric(func(x_grid, y_grid))
    z_payload = np.where(np.isfinite(z_grid), np.round(z_grid, 4), None).tolist()

    trace = TraceSpec(
        kind="contour",
        name="隐式曲线",
        x=x_values.round(4).tolist(),
        y=y_values.round(4).tolist(),
        z=z_payload,
        line={"color": CURVE_COLORS[0], "width": 3},
        contours={"start": 0, "end": 0, "size": 1, "coloring": "lines"},
        showscale=False,
    )

    return PlotSpec(
        plot_type="curve",
        expression_type="implicit2d",
        dimension="2d",
        title=f"二维隐式曲线：{expression}",
        summary="已生成二维隐式方程曲线。",
        axis_titles={"x": "x", "y": "y"},
        variables=["x", "y"],
        formulas=[expression],
        traces=[trace],
        parameter_ranges={"x": x_range, "y": y_range},
    )


def _build_spec(formulas: list[str], raw_text: str, implicit_expression: str | None = None) -> PlotSpec:
    parameter_ranges = parse_parameter_ranges(raw_text)
    if implicit_expression is not None:
        return _build_implicit_2d_spec(implicit_expression, parameter_ranges)
    expression_type = detect_expression_type(formulas)
    if expression_type == "parametric3d":
        return _build_parametric_3d_spec(formulas, parameter_ranges)
    if expression_type == "explicit3d":
        return _build_explicit_3d_spec(formulas, parameter_ranges)
    if expression_type == "parametric2d" and len(formulas) == 2 and {extract_expression(formula)[0] for formula in formulas} == {"x", "y"}:
        return _build_parametric_2d_spec(formulas, parameter_ranges)
    if expression_type == "polar2d":
        return _build_polar_2d_spec(formulas, parameter_ranges)
    return _build_explicit_2d_spec(formulas, parameter_ranges)


def _build_matlab_code(spec: PlotSpec) -> str:
    if spec.expression_type == "parametric3d":
        parameter = spec.variables[0]
        expressions = {extract_expression(formula)[0]: extract_expression(formula)[1].replace("**", ".^") for formula in spec.formulas}
        start, end = spec.parameter_ranges.get(parameter, (-6.0, 6.0))
        return "\n".join(
            [
                f"{parameter} = {start}:0.05:{end};",
                f"x = {expressions['x']};",
                f"y = {expressions['y']};",
                f"z = {expressions['z']};",
                "plot3(x, y, z, 'LineWidth', 2);",
                "xlabel('x'); ylabel('y'); zlabel('z');",
                "grid on; rotate3d on;",
            ]
        )

    if spec.expression_type == "parametric2d" and len(spec.formulas) == 2:
        parameter = spec.variables[0]
        start, end = spec.parameter_ranges.get(parameter, (-2 * math.pi, 2 * math.pi))
        expressions = {extract_expression(formula)[0]: extract_expression(formula)[1].replace("**", ".^") for formula in spec.formulas}
        return "\n".join(
            [
                f"{parameter} = {start}:0.05:{end};",
                f"x = {expressions['x']};",
                f"y = {expressions['y']};",
                "plot(x, y, 'LineWidth', 2);",
                "xlabel('x'); ylabel('y');",
                "grid on; axis equal;",
            ]
        )

    if spec.expression_type == "explicit3d":
        x_start, x_end = spec.parameter_ranges.get("x", (-4.0, 4.0))
        y_start, y_end = spec.parameter_ranges.get("y", (-4.0, 4.0))
        lines = [f"[x, y] = meshgrid({x_start}:0.1:{x_end}, {y_start}:0.1:{y_end});", "figure;", "hold on;"]
        for index, formula in enumerate(spec.formulas, start=1):
            _, expression = extract_expression(formula)
            lines.append(f"z{index} = {expression.replace('**', '.^')};")
            lines.append(f"surf(x, y, z{index}, 'FaceAlpha', {0.82 if len(spec.formulas) > 1 else 1.0});")
        lines.extend(["xlabel('x'); ylabel('y'); zlabel('z');", "grid on; rotate3d on;", "hold off;"])
        return "\n".join(lines)

    if spec.expression_type == "polar2d":
        start, end = spec.parameter_ranges.get("theta", (0.0, 2 * math.pi))
        _, expression = extract_expression(spec.formulas[0])
        return "\n".join(
            [
                f"theta = {start}:0.02:{end};",
                f"r = {expression.replace('**', '.^')};",
                "polarplot(theta, r, 'LineWidth', 2);",
                "grid on;",
            ]
        )

    if spec.expression_type == "implicit2d":
        x_start, x_end = spec.parameter_ranges.get("x", (-6.0, 6.0))
        y_start, y_end = spec.parameter_ranges.get("y", (-6.0, 6.0))
        expression = spec.formulas[0]
        if "=" in expression:
            left, right = expression.split("=", 1)
            matlab_expression = f"({left.strip().replace('**', '.^')}) - ({right.strip().replace('**', '.^')})"
        else:
            matlab_expression = expression.replace("**", ".^")
        return "\n".join(
            [
                f"[x, y] = meshgrid({x_start}:0.05:{x_end}, {y_start}:0.05:{y_end});",
                f"F = {matlab_expression};",
                "contour(x, y, F, [0 0], 'LineWidth', 2);",
                "xlabel('x'); ylabel('y');",
                "grid on; axis equal;",
            ]
        )

    axis_var = spec.axis_titles.get("x", "x")
    start, end = spec.parameter_ranges.get(axis_var, (-6.0, 6.0))
    lines = [f"{axis_var} = {start}:0.05:{end};", "figure;", "hold on;"]
    for formula in spec.formulas:
        left, expression = extract_expression(formula)
        matlab_expression = expression.replace("**", ".^")
        expr = _parse_expression(expression, SAFE_LOCALS)
        parameter_symbol = _extract_parameter_symbol(expr, excluded={left})
        if parameter_symbol is not None:
            lines[0] = f"{parameter_symbol} = {start}:0.05:{end};"
            lines.append(f"plot({parameter_symbol}, {matlab_expression}, 'LineWidth', 2);")
        elif left == "y":
            lines.append(f"plot(x, {matlab_expression}, 'LineWidth', 2);")
        else:
            lines.append("y = x;")
            lines.append(f"plot({matlab_expression}, y, 'LineWidth', 2);")
    lines.extend([f"xlabel('{spec.axis_titles.get('x', 'x')}'); ylabel('{spec.axis_titles.get('y', 'y')}');", "grid on;", "hold off;"])
    return "\n".join(lines)


def _build_teaching_tip(spec: PlotSpec) -> str:
    joined = "、".join(normalize_formula_text(formula) for formula in spec.formulas)
    if spec.expression_type == "parametric3d":
        return f"这组参数方程适合配合参数变化讲解空间轨迹：{joined}。"
    if spec.expression_type == "parametric2d":
        return f"这组参数曲线适合讲解轨迹方向、闭合性和参数区间：{joined}。"
    if spec.expression_type == "explicit3d":
        return f"这组曲面适合对比开口方向、对称性和交线：{joined}。"
    if spec.expression_type == "polar2d":
        return f"这张极坐标图适合讲解角度和半径之间的关系：{joined}。"
    if spec.expression_type == "implicit2d":
        return f"这张隐式曲线适合讲解等值线、对称性和约束边界：{joined}。"
    if len(spec.formulas) > 1:
        return f"这组函数可以联动讲解交点、相对位置和变化趋势：{joined}。"
    return f"这张函数图适合讲解零点、极值与变化趋势：{joined}。"


def _resolve_plot_label(plot_type: str) -> str:
    mapping = {
        "curve": "二维图像",
        "multi_curve": "二维多图层图像",
        "surface": "三维曲面",
        "multi_surface": "三维曲面叠加",
        "parametric3d": "三维参数曲线",
    }
    return mapping.get(plot_type, "数学绘图")


def _normalize_plot_copy(spec: PlotSpec) -> PlotSpec:
    joined = "、".join(normalize_formula_text(formula) for formula in spec.formulas) or spec.title
    summary_map = {
        "explicit2d": "已生成二维函数图像。",
        "parametric2d": "已生成二维参数曲线。",
        "explicit3d": "已生成三维曲面图像。" if len(spec.formulas) == 1 else "已生成三维曲面叠加图像。",
        "parametric3d": "已生成三维参数曲线。",
        "polar2d": "已生成极坐标曲线。",
        "implicit2d": "已生成二维隐式方程曲线。",
    }
    tip_map = {
        "parametric3d": f"这组参数方程适合讲解空间轨迹与参数变化：{joined}。",
        "parametric2d": f"这组参数曲线适合讲解轨迹方向、闭合性和参数区间：{joined}。",
        "explicit3d": f"这组曲面适合讲解开口方向、对称性和交线：{joined}。",
        "polar2d": f"这张极坐标图适合讲解角度和半径的关系：{joined}。",
        "implicit2d": f"这张隐式曲线适合讲解等值线、对称性和约束边界：{joined}。",
        "explicit2d": (
            f"这组函数可以联动讲解交点、相对位置和变化趋势：{joined}。"
            if len(spec.formulas) > 1
            else f"这张函数图适合讲解零点、极值与变化趋势：{joined}。"
        ),
    }
    label_map = {
        "curve": "二维图像",
        "multi_curve": "二维多图层图像",
        "surface": "三维曲面",
        "multi_surface": "三维曲面叠加",
        "parametric3d": "三维参数曲线",
    }

    if spec.expression_type == "explicit2d":
        spec.title = f"二维图像：{joined}"
    elif spec.expression_type == "parametric2d":
        spec.title = f"二维参数曲线：{joined}"
    elif spec.expression_type == "explicit3d":
        spec.title = f"三维图像：{joined}"
    elif spec.expression_type == "parametric3d":
        spec.title = f"三维参数曲线：{joined}"
    elif spec.expression_type == "polar2d":
        spec.title = f"极坐标图像：{joined}"
    elif spec.expression_type == "implicit2d":
        spec.title = f"二维隐式曲线：{joined}"

    spec.summary = summary_map.get(spec.expression_type, spec.summary)
    spec.teaching_tip = tip_map.get(spec.expression_type, spec.teaching_tip)
    spec.plot_label = label_map.get(spec.plot_type, "数学绘图")
    return spec


def _append_point_annotations(spec: PlotSpec, text: str) -> PlotSpec:
    point_annotations = extract_point_annotations(text)
    if not point_annotations:
        return spec

    filtered = [item for item in point_annotations if item["dimension"] == spec.dimension]
    if not filtered:
        return spec

    if spec.dimension == "3d":
        spec.traces.append(
            TraceSpec(
                kind="scatter3d",
                name="标注点",
                mode="markers+text",
                x=[round(item["coords"][0], 4) for item in filtered],
                y=[round(item["coords"][1], 4) for item in filtered],
                z=[round(item["coords"][2], 4) for item in filtered],
                text=[item["name"] for item in filtered],
                marker={"size": 5, "color": "#dc2626", "line": {"width": 1, "color": "#7f1d1d"}},
            )
        )
    else:
        spec.traces.append(
            TraceSpec(
                kind="scatter",
                name="标注点",
                mode="markers+text",
                x=[round(item["coords"][0], 4) for item in filtered],
                y=[round(item["coords"][1], 4) for item in filtered],
                text=[item["name"] for item in filtered],
                marker={"size": 10, "color": "#dc2626", "line": {"width": 1, "color": "#7f1d1d"}},
            )
        )
    spec.annotations.extend(filtered)
    return spec


def _append_matlab_annotations(spec: PlotSpec) -> PlotSpec:
    if not spec.annotations:
        return spec

    lines = [spec.matlab_code.rstrip()]
    if spec.dimension == "3d":
        xs = ", ".join(str(item["coords"][0]) for item in spec.annotations if item["dimension"] == "3d")
        ys = ", ".join(str(item["coords"][1]) for item in spec.annotations if item["dimension"] == "3d")
        zs = ", ".join(str(item["coords"][2]) for item in spec.annotations if item["dimension"] == "3d")
        if xs and ys and zs:
            lines.extend(
                [
                    "",
                    f"scatter3([{xs}], [{ys}], [{zs}], 60, 'filled', 'MarkerFaceColor', [0.86 0.15 0.15]);",
                    "text(["
                    + xs
                    + "], ["
                    + ys
                    + "], ["
                    + zs
                    + "], {"
                    + ", ".join(f"'{item['name']}'" for item in spec.annotations if item["dimension"] == "3d")
                    + "});",
                ]
            )
    else:
        xs = ", ".join(str(item["coords"][0]) for item in spec.annotations if item["dimension"] == "2d")
        ys = ", ".join(str(item["coords"][1]) for item in spec.annotations if item["dimension"] == "2d")
        if xs and ys:
            lines.extend(
                [
                    "",
                    f"scatter([{xs}], [{ys}], 60, 'filled', 'MarkerFaceColor', [0.86 0.15 0.15]);",
                    "text(["
                    + xs
                    + "], ["
                    + ys
                    + "], {"
                    + ", ".join(f"'{item['name']}'" for item in spec.annotations if item["dimension"] == "2d")
                    + "});",
                ]
            )
    spec.matlab_code = "\n".join(lines)
    return spec


def _append_plot_metadata(spec: PlotSpec) -> PlotSpec:
    spec.matlab_code = _build_matlab_code(spec)
    spec.teaching_tip = _build_teaching_tip(spec)
    spec.plot_label = _resolve_plot_label(spec.plot_type)
    spec = _normalize_plot_copy(spec)
    spec = _append_matlab_annotations(spec)
    return spec


def _apply_trace_filters(trace: TraceSpec, filters: dict[str, tuple[float, float] | None]) -> TraceSpec:
    updated = TraceSpec(**asdict(trace))
    if trace.kind == "surface" and trace.x is not None and trace.y is not None and trace.z is not None:
        x = np.asarray(trace.x, dtype=float)
        y = np.asarray(trace.y, dtype=float)
        z = np.asarray(trace.z, dtype=float)
        mask = np.ones_like(z, dtype=bool)
        for axis, bounds in filters.items():
            if bounds is None:
                continue
            lower, upper = bounds
            values = {"x": x, "y": y, "z": z}[axis]
            mask &= values >= lower
            if math.isfinite(upper):
                mask &= values <= upper
        updated.z = np.where(mask, z, np.nan).tolist()
        return updated

    axes: dict[str, np.ndarray] = {}
    for axis in ("x", "y", "z"):
        values = getattr(trace, axis)
        if values is not None and isinstance(values, list) and (not values or not isinstance(values[0], list)):
            axes[axis] = np.asarray(values, dtype=float)

    if not axes:
        return updated

    mask = np.ones(len(next(iter(axes.values()))), dtype=bool)
    for axis, bounds in filters.items():
        values = axes.get(axis)
        if values is None or bounds is None:
            continue
        lower, upper = bounds
        mask &= values >= lower
        if math.isfinite(upper):
            mask &= values <= upper

    for axis, values in axes.items():
        setattr(updated, axis, values[mask].round(4).tolist())
    if updated.text is not None:
        updated.text = [value for value, keep in zip(updated.text, mask) if keep]
    return updated


def apply_plot_edit(previous_plot: dict[str, Any], text: str) -> dict[str, Any]:
    filters = parse_axis_filters(text)
    if not filters:
        raise ValueError("未识别到可执行的图像修改指令。当前支持按 x/y/z 正半轴或负半轴裁剪。")

    plot_spec_payload = previous_plot.get("plot_spec")
    if plot_spec_payload:
        traces = [TraceSpec(**trace) for trace in plot_spec_payload.get("traces", [])]
        spec = PlotSpec(
            plot_type=plot_spec_payload.get("plot_type", previous_plot.get("plot_type", "curve")),
            expression_type=plot_spec_payload.get("expression_type", previous_plot.get("expression_type", "explicit2d")),
            dimension=plot_spec_payload.get("dimension", previous_plot.get("dimension", "2d")),
            title=plot_spec_payload.get("title", previous_plot.get("layout", {}).get("title", "数学绘图")),
            summary=plot_spec_payload.get("summary", previous_plot.get("summary", "")),
            axis_titles=plot_spec_payload.get("axis_titles", {"x": "x", "y": "y"}),
            variables=plot_spec_payload.get("variables", []),
            formulas=plot_spec_payload.get("formulas", previous_plot.get("formulas", [])),
            traces=traces,
            parameter_ranges=plot_spec_payload.get("parameter_ranges", {}),
            annotations=plot_spec_payload.get("annotations", []),
            matlab_code=plot_spec_payload.get("matlab_code", previous_plot.get("matlab_code", "")),
            teaching_tip=plot_spec_payload.get("teaching_tip", previous_plot.get("teaching_tip", "")),
            plot_label=plot_spec_payload.get("plot_label", previous_plot.get("plot_label", "数学绘图")),
        )
    else:
        spec = PlotSpec(
            plot_type=previous_plot.get("plot_type", "curve"),
            expression_type=previous_plot.get("expression_type", "explicit2d"),
            dimension=previous_plot.get("dimension", "2d"),
            title=previous_plot.get("layout", {}).get("title", "数学绘图"),
            summary=previous_plot.get("summary", ""),
            axis_titles={
                "x": previous_plot.get("layout", {}).get("xaxis", {}).get("title", "x"),
                "y": previous_plot.get("layout", {}).get("yaxis", {}).get("title", "y"),
                "z": previous_plot.get("layout", {}).get("scene", {}).get("zaxis", {}).get("title", "z"),
            },
            variables=[],
            formulas=previous_plot.get("formulas", []),
            traces=[],
        )

    spec.traces = [_apply_trace_filters(trace, filters) for trace in spec.traces]
    spec.summary = f"已根据指令裁剪图像：{text.strip()}"
    spec.matlab_code = spec.matlab_code + "\n% 当前图像已做局部裁剪"
    spec.teaching_tip = "这是基于上一张图进行的局部修改，适合讲解定义域、观察窗口和局部性质。"
    spec.plot_label = f"{spec.plot_label}（已修改）"
    return _spec_to_bundle(spec)


def build_plot_bundle(text: str, previous_plot: dict[str, Any] | None = None) -> dict[str, Any]:
    if should_edit_existing_plot(text, previous_plot):
        return apply_plot_edit(previous_plot, text)

    formulas = extract_formula_texts(text)
    implicit_expression = None
    if not formulas:
        implicit_expression = _extract_implicit_expression(text)
        formulas = [normalize_formula_text(text)] if implicit_expression is None else [implicit_expression]

    spec = _build_spec(formulas, text, implicit_expression=implicit_expression)
    spec = _append_point_annotations(spec, text)
    spec = _append_plot_metadata(spec)
    return _spec_to_bundle(spec)
