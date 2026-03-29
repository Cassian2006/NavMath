import pytest

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


PLOT_CASES = [
    ("y = x", "explicit2d", "curve", "scatter"),
    ("y = x^2", "explicit2d", "curve", "scatter"),
    ("y = x^3 - 3x", "explicit2d", "curve", "scatter"),
    ("y = 1/x", "explicit2d", "curve", "scatter"),
    ("y = sqrt(x)", "explicit2d", "curve", "scatter"),
    ("y = abs(x)", "explicit2d", "curve", "scatter"),
    ("y = sin(x)", "explicit2d", "curve", "scatter"),
    ("y = cos(x)", "explicit2d", "curve", "scatter"),
    ("y = tan(x)", "explicit2d", "curve", "scatter"),
    ("y = e^x", "explicit2d", "curve", "scatter"),
    ("y = ln(x)", "explicit2d", "curve", "scatter"),
    ("y = x*sin(x)", "explicit2d", "curve", "scatter"),
    ("y = sin(1/x)", "explicit2d", "curve", "scatter"),
    ("y = x/(1+x^2)", "explicit2d", "curve", "scatter"),
    ("y = floor(x)", "explicit2d", "curve", "scatter"),
    ("z = x + y", "explicit3d", "surface", "surface"),
    ("z = x^2 + y^2", "explicit3d", "surface", "surface"),
    ("z = x^2 - y^2", "explicit3d", "surface", "surface"),
    ("z = sin(x)*cos(y)", "explicit3d", "surface", "surface"),
    ("z = exp(-(x^2 + y^2))", "explicit3d", "surface", "surface"),
    ("z = sqrt(x^2 + y^2)", "explicit3d", "surface", "surface"),
    ("z = ln(x^2 + y^2 + 1)", "explicit3d", "surface", "surface"),
    ("z = x*y", "explicit3d", "surface", "surface"),
    ("z = sin(sqrt(x^2 + y^2))", "explicit3d", "surface", "surface"),
    ("z = 1/(1 + x^2 + y^2)", "explicit3d", "surface", "surface"),
    ("x = t, y = t^2", "parametric2d", "curve", "scatter"),
    ("x = cos(t), y = sin(t)", "parametric2d", "curve", "scatter"),
    ("x = 2*cos(t), y = sin(t)", "parametric2d", "curve", "scatter"),
    ("x = cos(2t), y = sin(3t)", "parametric2d", "curve", "scatter"),
    ("x = t*cos(t), y = t*sin(t)", "parametric2d", "curve", "scatter"),
    ("x = sin(t), y = t", "parametric2d", "curve", "scatter"),
    ("x = t - sin(t), y = 1 - cos(t)", "parametric2d", "curve", "scatter"),
    ("x = cos(t)^3, y = sin(t)^3", "parametric2d", "curve", "scatter"),
    ("x = (1+0.5*cos(8t))*cos(t), y = (1+0.5*cos(8t))*sin(t)", "parametric2d", "curve", "scatter"),
    ("x = sin(3t), y = sin(4t)", "parametric2d", "curve", "scatter"),
    ("r = 1", "polar2d", "curve", "scatter"),
    ("r = 2*cos(theta)", "polar2d", "curve", "scatter"),
    ("r = 2*sin(theta)", "polar2d", "curve", "scatter"),
    ("r = 1 + cos(theta)", "polar2d", "curve", "scatter"),
    ("r = 1 + 2*sin(theta)", "polar2d", "curve", "scatter"),
    ("r = cos(4theta)", "polar2d", "curve", "scatter"),
    ("r = theta", "polar2d", "curve", "scatter"),
    ("x^2 + y^2 = 1", "implicit2d", "curve", "contour"),
    ("x^2/4 + y^2 = 1", "implicit2d", "curve", "contour"),
    ("x^2 - y^2 = 1", "implicit2d", "curve", "contour"),
    ("xy = 1", "implicit2d", "curve", "contour"),
    ("x^3 - y^2 = 0", "implicit2d", "curve", "contour"),
    ("x^(2/3) + y^(2/3) = 1", "implicit2d", "curve", "contour"),
    ("sin(x) + cos(y) = 0", "implicit2d", "curve", "contour"),
    ("x^4 + y^4 = 1", "implicit2d", "curve", "contour"),
]


@pytest.mark.parametrize(("formula", "expression_type", "plot_type", "trace_type"), PLOT_CASES)
def test_plot_catalog_cases_support_plot_and_matlab(formula, expression_type, plot_type, trace_type) -> None:
    response = client.post("/api/analyze-text", data={"question_text": f"请画 {formula}"})

    body = response.json()
    plot = body["plot"]

    assert response.status_code == 200
    assert plot["plot_type"] == plot_type
    assert plot["expression_type"] == expression_type
    assert plot["data"]
    assert plot["data"][0]["type"] == trace_type
    assert plot["matlab_code"].strip()
