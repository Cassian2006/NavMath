from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_formula_question_returns_plot() -> None:
    response = client.post(
        "/api/analyze-text",
        data={"question_text": "判断曲面 z = x^2 - y^2 的类型"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["formula"] == "z = x^2 - y^2"
    assert body["plot"]["plot_type"] == "surface"
