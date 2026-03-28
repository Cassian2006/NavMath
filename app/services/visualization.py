from __future__ import annotations

import math
from typing import Any


MESH_SIZE = 48
LINE_SIZE = 240

SHAPE_ALIASES = {
    "sphere": ["sphere", "球", "球面"],
    "cylinder": ["cylinder", "圆柱", "圆柱面"],
    "cone": ["cone", "圆锥", "圆锥面"],
    "torus": ["torus", "圆环", "圆环面"],
    "helix": ["helix", "螺旋线", "螺旋"],
    "saddle": ["saddle", "鞍面", "双曲抛物面"],
    "wave": ["wave", "波浪", "波浪面", "正弦曲面"],
}


def build_shape_bundle(text: str) -> dict[str, Any] | None:
    kind = resolve_shape_kind(text)
    if not kind:
        return None
    return build_shape_bundle_from_kind(kind)


def build_shape_bundle_from_kind(kind: str) -> dict[str, Any] | None:
    if kind not in SHAPE_ALIASES:
        return None

    if kind == "helix":
        geometry = helix_geometry()
        return {
            "plot_type": "helix",
            "plot_label": "三维演示",
            "data": [
                {
                    "type": "scatter3d",
                    "mode": "lines",
                    "x": geometry["x"],
                    "y": geometry["y"],
                    "z": geometry["z"],
                    "line": {"width": 6, "color": geometry["z"], "colorscale": "Cividis"},
                    "name": "螺旋线",
                }
            ],
            "layout": _scene_layout("三维图形演示: 螺旋线"),
            "summary": "已根据文本匹配到螺旋线演示图形，可用于空间曲线教学展示。",
            "matlab_code": "\n".join(
                [
                    "t = linspace(0, 8*pi, 240);",
                    "plot3(cos(t), sin(t), t/pi, 'LineWidth', 2);",
                    "grid on; axis equal;",
                    "xlabel('X'); ylabel('Y'); zlabel('Z');",
                ]
            ),
            "teaching_tip": "该图形适合用于演示参数曲线、空间轨迹和旋转上升过程。",
        }

    x, y, z = surface_geometry(kind)
    return {
        "plot_type": "surface",
        "plot_label": "三维演示",
        "data": [
            {
                "type": "surface",
                "x": x,
                "y": y,
                "z": z,
                "colorscale": _colorscale(kind),
                "showscale": False,
            }
        ],
        "layout": _scene_layout(f"三维图形演示: {display_name(kind)}"),
        "summary": f"已根据文本匹配到 {display_name(kind)} 的三维演示图形。",
        "matlab_code": matlab_code_for_shape(kind),
        "teaching_tip": f"该图形适合用于演示 {display_name(kind)} 的几何特征、截面变化和空间形态。",
    }


def resolve_shape_kind(text: str) -> str | None:
    lower_text = text.lower()
    for kind, aliases in SHAPE_ALIASES.items():
        if any(alias.lower() in lower_text or alias in text for alias in aliases):
            return kind
    return None


def display_name(kind: str) -> str:
    mapping = {
        "sphere": "球面",
        "cylinder": "圆柱面",
        "cone": "圆锥面",
        "torus": "圆环面",
        "helix": "螺旋线",
        "saddle": "鞍面",
        "wave": "波浪曲面",
    }
    return mapping[kind]


def surface_geometry(kind: str) -> tuple[list[Any], list[Any], list[Any]]:
    if kind == "sphere":
        return sphere_surface(4.0)
    if kind == "cylinder":
        return cylinder_surface(1.8, 4.0)
    if kind == "cone":
        return cone_surface(2.2, 4.5)
    if kind == "torus":
        return torus_surface(3.2, 1.1)
    if kind == "saddle":
        return sampled_surface(-4.0, 4.0, lambda xv, yv: (xv * xv - yv * yv) / 3.0)
    return sampled_surface(-8.0, 8.0, lambda xv, yv: 2.2 * math.sin(xv / 1.7) * math.cos(yv / 2.1))


def sampled_surface(start: float, end: float, fn) -> tuple[list[float], list[float], list[list[float]]]:
    x = linspace(start, end, MESH_SIZE)
    y = linspace(start, end, MESH_SIZE)
    z = [[fn(xv, yv) for xv in x] for yv in y]
    return x, y, z


def sphere_surface(radius: float) -> tuple[list[Any], list[Any], list[Any]]:
    theta = linspace(0.0, math.pi, MESH_SIZE)
    phi = linspace(0.0, 2.0 * math.pi, MESH_SIZE)
    x, y, z = [], [], []
    for t in theta:
        row_x, row_y, row_z = [], [], []
        for p in phi:
            row_x.append(radius * math.sin(t) * math.cos(p))
            row_y.append(radius * math.sin(t) * math.sin(p))
            row_z.append(radius * math.cos(t))
        x.append(row_x)
        y.append(row_y)
        z.append(row_z)
    return x, y, z


def cylinder_surface(radius: float, height: float) -> tuple[list[Any], list[Any], list[Any]]:
    theta = linspace(0.0, 2.0 * math.pi, MESH_SIZE)
    z_axis = linspace(-height / 2.0, height / 2.0, MESH_SIZE)
    x, y, z = [], [], []
    for zv in z_axis:
        row_x, row_y, row_z = [], [], []
        for t in theta:
            row_x.append(radius * math.cos(t))
            row_y.append(radius * math.sin(t))
            row_z.append(zv)
        x.append(row_x)
        y.append(row_y)
        z.append(row_z)
    return x, y, z


def cone_surface(radius: float, height: float) -> tuple[list[Any], list[Any], list[Any]]:
    theta = linspace(0.0, 2.0 * math.pi, MESH_SIZE)
    z_axis = linspace(-height / 2.0, height / 2.0, MESH_SIZE)
    x, y, z = [], [], []
    for zv in z_axis:
        scale = max(0.0, 1.0 - (zv + height / 2.0) / height)
        row_x, row_y, row_z = [], [], []
        for t in theta:
            row_x.append(radius * scale * math.cos(t))
            row_y.append(radius * scale * math.sin(t))
            row_z.append(zv)
        x.append(row_x)
        y.append(row_y)
        z.append(row_z)
    return x, y, z


def torus_surface(major_radius: float, minor_radius: float) -> tuple[list[Any], list[Any], list[Any]]:
    u = linspace(0.0, 2.0 * math.pi, MESH_SIZE)
    v = linspace(0.0, 2.0 * math.pi, MESH_SIZE)
    x, y, z = [], [], []
    for vv in v:
        row_x, row_y, row_z = [], [], []
        for uu in u:
            ring = major_radius + minor_radius * math.cos(vv)
            row_x.append(ring * math.cos(uu))
            row_y.append(ring * math.sin(uu))
            row_z.append(minor_radius * math.sin(vv))
        x.append(row_x)
        y.append(row_y)
        z.append(row_z)
    return x, y, z


def helix_geometry() -> dict[str, list[float]]:
    t = linspace(0.0, 8.0 * math.pi, LINE_SIZE)
    return {
        "x": [math.cos(tv) for tv in t],
        "y": [math.sin(tv) for tv in t],
        "z": [tv / math.pi for tv in t],
    }


def matlab_code_for_shape(kind: str) -> str:
    code_map = {
        "sphere": [
            "[X, Y, Z] = sphere(44);",
            "surf(4 * X, 4 * Y, 4 * Z);",
            "shading interp; axis equal; grid on;",
        ],
        "cylinder": [
            "[X, Y, Z] = cylinder(1.8, 44);",
            "surf(X, Y, 4 * Z - 2);",
            "shading interp; axis equal; grid on;",
        ],
        "cone": [
            "[X, Y, Z] = cylinder([2.2 0], 44);",
            "surf(X, Y, 4.5 * Z - 2.25);",
            "shading interp; axis equal; grid on;",
        ],
        "torus": [
            "[U, V] = meshgrid(linspace(0, 2*pi, 45));",
            "X = (3.2 + 1.1*cos(V)) .* cos(U);",
            "Y = (3.2 + 1.1*cos(V)) .* sin(U);",
            "Z = 1.1 * sin(V);",
            "surf(X, Y, Z); shading interp; axis equal;",
        ],
        "saddle": [
            "[X, Y] = meshgrid(linspace(-4, 4, 45));",
            "Z = (X.^2 - Y.^2) / 3;",
            "surf(X, Y, Z); shading interp; grid on;",
        ],
        "wave": [
            "[X, Y] = meshgrid(linspace(-8, 8, 45));",
            "Z = 2.2 * sin(X / 1.7) .* cos(Y / 2.1);",
            "surf(X, Y, Z); shading interp; grid on;",
        ],
    }
    return "\n".join(code_map[kind])


def _scene_layout(title: str) -> dict[str, Any]:
    return {
        "title": title,
        "paper_bgcolor": "#ffffff",
        "margin": {"l": 0, "r": 0, "t": 56, "b": 0},
        "scene": {
            "xaxis": {"title": "x", "backgroundcolor": "#f8fafc"},
            "yaxis": {"title": "y", "backgroundcolor": "#f8fafc"},
            "zaxis": {"title": "z", "backgroundcolor": "#f8fafc"},
            "camera": {"eye": {"x": 1.45, "y": 1.45, "z": 0.9}},
        },
    }


def _colorscale(kind: str) -> str:
    mapping = {
        "sphere": "Turbo",
        "cylinder": "Blues",
        "cone": "Reds",
        "torus": "Viridis",
        "saddle": "RdBu",
        "wave": "Portland",
    }
    return mapping[kind]


def linspace(start: float, end: float, count: int) -> list[float]:
    step = (end - start) / (count - 1)
    return [start + step * index for index in range(count)]
