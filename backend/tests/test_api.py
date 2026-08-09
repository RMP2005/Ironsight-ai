"""HTTP integration tests for the IronSight AI FastAPI backend."""

import pytest
from fastapi.testclient import TestClient

from backend.app.decision import get_maintenance_recommendation
from backend.app.main import app, get_risk_level


client = TestClient(app)

LOW_RECOMMENDATION = (
    "Continue routine monitoring; no immediate maintenance action is indicated by the model."
)
MODERATE_RECOMMENDATION = (
    "Consider scheduling a routine inspection and continue monitoring operating conditions."
)
HIGH_RECOMMENDATION = (
    "Prioritize engineering inspection and review recent operating conditions before continued operation."
)

IN_RANGE_PAYLOAD = {
    "air_temperature": 298.1,
    "process_temperature": 308.6,
    "rotational_speed": 1551.0,
    "torque": 42.8,
    "tool_wear": 0.0,
}

OUT_OF_RANGE_PAYLOAD = {
    **IN_RANGE_PAYLOAD,
    "torque": 95.0,
    "tool_wear": 300.0,
}


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_model_info_endpoint():
    response = client.get("/model-info")
    body = response.json()

    assert response.status_code == 200
    assert body["is_loaded"] is True
    assert body["threshold"] == pytest.approx(0.6)
    assert body["target_name"] == "Machine failure"
    assert body["feature_names"] == [
        "Air temperature [K]",
        "Process temperature [K]",
        "Rotational speed [rpm]",
        "Torque [Nm]",
        "Tool wear [min]",
    ]
    assert set(body["feature_units"]) == set(body["feature_names"])
    assert set(body["feature_ranges"]) == set(body["feature_names"])
    for feature_name in body["feature_names"]:
        range_info = body["feature_ranges"][feature_name]
        assert {"min", "max", "unit"} <= set(range_info)
        assert range_info["unit"] == body["feature_units"][feature_name]


def test_predict_in_range_input():
    response = client.post("/predict", json=IN_RANGE_PAYLOAD)
    body = response.json()

    assert response.status_code == 200
    assert body["failure_probability"] == pytest.approx(0.000196737, abs=1e-9)
    assert body["threshold"] == pytest.approx(0.6)
    assert body["failure_alert"] is False
    assert body["risk_level"] == "Low"
    assert body["maintenance_recommendation"] == LOW_RECOMMENDATION
    assert body["validation_warnings"] == []


def test_predict_out_of_range_input():
    response = client.post("/predict", json=OUT_OF_RANGE_PAYLOAD)
    body = response.json()

    assert response.status_code == 200
    assert body["failure_probability"] == pytest.approx(0.8956545, abs=1e-6)
    assert body["threshold"] == pytest.approx(0.6)
    assert body["failure_alert"] is True
    assert body["risk_level"] == "High"
    assert body["maintenance_recommendation"] == HIGH_RECOMMENDATION
    assert len(body["validation_warnings"]) == 2
    assert "Torque [Nm]" in body["validation_warnings"][0]
    assert "Tool wear [min]" in body["validation_warnings"][1]


@pytest.mark.parametrize(
    ("probability", "expected_risk_level"),
    [
        (0.10, "Low"),
        (0.299999, "Low"),
        (0.30, "Moderate"),
        (0.599999, "Moderate"),
        (0.60, "High"),
        (0.90, "High"),
    ],
)
def test_risk_boundaries(probability, expected_risk_level):
    assert get_risk_level(probability) == expected_risk_level


@pytest.mark.parametrize(
    ("risk_level", "expected_recommendation"),
    [
        ("Low", LOW_RECOMMENDATION),
        ("Moderate", MODERATE_RECOMMENDATION),
        ("High", HIGH_RECOMMENDATION),
    ],
)
def test_maintenance_recommendations(risk_level, expected_recommendation):
    assert get_maintenance_recommendation(risk_level) == expected_recommendation


@pytest.mark.parametrize(
    "payload",
    [
        {key: value for key, value in IN_RANGE_PAYLOAD.items() if key != "tool_wear"},
        {**IN_RANGE_PAYLOAD, "torque": "banana"},
    ],
)
def test_predict_rejects_malformed_input(payload):
    response = client.post("/predict", json=payload)

    assert 400 <= response.status_code < 500
    assert response.status_code == 422
