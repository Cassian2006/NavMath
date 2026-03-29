import json
import math

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_formula_question_returns_surface_plot() -> None:
    response = client.post(
        "/api/analyze-text",
        data={"question_text": "判断曲面 z = x^2 - y^2 的类型"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["formula"] == "z = x^2 - y^2"
    assert body["plot"]["plot_type"] == "surface"
    assert body["plot"]["expression_type"] == "explicit3d"


def test_parametric_3d_curve_is_supported() -> None:
    response = client.post(
        "/api/analyze-text",
        data={"question_text": "请画 x = cos(t), y = sin(t), z = t"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["plot"]["plot_type"] == "parametric3d"
    assert body["plot"]["data"][0]["type"] == "scatter3d"
    assert body["plot"]["expression_type"] == "parametric3d"


def test_single_parametric_component_is_supported() -> None:
    response = client.post(
        "/api/analyze-text",
        data={"question_text": "请画 x = cos(t)"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["plot"]["plot_type"] == "curve"
    assert body["plot"]["data"][0]["type"] == "scatter"
    assert body["plot"]["layout"]["xaxis"]["title"] == "t"
    assert body["plot"]["layout"]["yaxis"]["title"] == "x"
    assert body["plot"]["data"][0]["name"] == "x(t)"
    assert body["plot"]["plot_spec"]["expression_type"] == "explicit2d"


def test_single_parametric_component_with_custom_parameter_is_supported() -> None:
    response = client.post(
        "/api/analyze-text",
        data={"question_text": "请画 x = cos(u)"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["plot"]["plot_type"] == "curve"
    assert body["plot"]["layout"]["xaxis"]["title"] == "u"


def test_parametric_2d_curve_is_supported() -> None:
    response = client.post(
        "/api/analyze-text",
        data={"question_text": "请画 x = cos(t), y = sin(t), t in [0, 2*pi]"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["plot"]["plot_type"] == "curve"
    assert body["plot"]["expression_type"] == "parametric2d"
    assert body["plot"]["plot_spec"]["variables"] == ["t"]
    assert math.isclose(body["plot"]["plot_spec"]["parameter_ranges"]["t"][1], 2 * math.pi)


def test_implicit_2d_curve_is_supported() -> None:
    response = client.post(
        "/api/analyze-text",
        data={"question_text": "请画 x^2 + y^2 = 4"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["plot"]["plot_type"] == "curve"
    assert body["plot"]["expression_type"] == "implicit2d"
    assert body["plot"]["data"][0]["type"] == "contour"


def test_curve_can_include_point_annotations() -> None:
    response = client.post(
        "/api/analyze-text",
        data={"question_text": "请画 y = x^2，并标注点 (1, 1)"},
    )

    body = response.json()
    assert response.status_code == 200
    assert any(trace["name"] == "标注点" for trace in body["plot"]["data"])
    assert body["plot"]["plot_spec"]["annotations"]
    assert "scatter(" in body["plot"]["matlab_code"]


def test_two_functions_can_overlay_and_mark_intersections() -> None:
    response = client.post(
        "/api/analyze-text",
        data={"question_text": "请在同一张图上画 y = x^2 和 y = 2 - x^2"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["plot"]["plot_type"] == "multi_curve"
    assert len(body["plot"]["data"]) >= 3
    assert any(trace.get("name") == "交点" for trace in body["plot"]["data"])
    assert body["plot"]["plot_spec"]["traces"][0]["name"] == "y = x^2"


def test_two_surfaces_can_overlay() -> None:
    response = client.post(
        "/api/analyze-text",
        data={"question_text": "曲面 z = x^2 - y^2，z = x^2 - y^3"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["plot"]["plot_type"] == "multi_surface"
    surface_traces = [trace for trace in body["plot"]["data"] if trace["type"] == "surface"]
    assert len(surface_traces) == 2
    assert all(trace["showlegend"] for trace in surface_traces)
    assert surface_traces[0]["hidesurface"] is False
    assert surface_traces[1]["hidesurface"] is True
    assert surface_traces[1]["contours"]["z"]["width"] == 3
    assert body["plot"]["plot_spec"]["expression_type"] == "explicit3d"


def test_plot_can_be_modified_from_previous_state() -> None:
    first_response = client.post(
        "/api/analyze-text",
        data={"question_text": "请画 y = x^2"},
    )
    first_body = first_response.json()

    second_response = client.post(
        "/api/analyze-text",
        data={
            "question_text": "只保留这张图的 x 正半轴部分",
            "previous_plot": json.dumps(first_body["plot"], ensure_ascii=False),
        },
    )
    second_body = second_response.json()

    assert second_response.status_code == 200
    assert second_body["plot"]["plot_label"].endswith("（已修改）")
    x_values = second_body["plot"]["data"][0]["x"]
    assert x_values
    assert min(x_values) >= 0
    assert second_body["plot"]["plot_spec"]["traces"][0]["x"]


def test_invalid_formula_returns_plot_error_message() -> None:
    response = client.post(
        "/api/analyze-text",
        data={"question_text": "请画 y = foo(x)"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["plot"]["plot_type"] == "unsupported"
    assert body["plot"]["error_detail"]


def test_polar_curve_with_implicit_multiplication_is_supported() -> None:
    response = client.post(
        "/api/analyze-text",
        data={"question_text": "???????? r = 1 + 2cos(theta)?"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["plot"]["plot_type"] == "curve"
    assert body["plot"]["expression_type"] == "polar2d"
    assert body["plot"]["data"][0]["type"] == "scatter"
    assert math.isclose(body["plot"]["plot_spec"]["parameter_ranges"]["theta"][1], 2 * math.pi)
