"""
backend/app/main.py — IronSight AI Backend API

FastAPI application providing health check, metadata verification, and prediction endpoints with range validation.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.schemas import PredictionRequest, PredictionResponse
from backend.app.predictor import (
    get_model_metadata,
    get_model_threshold,
    predict_failure_probability,
)
from backend.app.decision import get_maintenance_recommendation
from backend.app.validator import validate_sensor_ranges

DEFAULT_CORS_ORIGINS = "http://localhost:3000"


def get_cors_origins() -> list[str]:
    """Parse exact CORS origins from CORS_ORIGINS (comma-separated). Never uses '*'."""
    raw = os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins if origins else [DEFAULT_CORS_ORIGINS]


app = FastAPI(
    title="IronSight AI Backend",
    description="Predictive Maintenance API for Industrial Machine Failures",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def get_risk_level(probability: float) -> str:
    """Classifies probability using prototype application-level risk boundaries."""
    if probability < 0.30:
        return "Low"
    if probability < 0.60:
        return "Moderate"
    return "High"


@app.get("/")
def read_root():
    """Root endpoint returning backend project name and operational status."""
    return {
        "project": "IronSight AI",
        "status": "Backend Running",
    }


@app.get("/health")
def health_check():
    """Health check endpoint for service monitoring."""
    return {
        "status": "ok",
    }


@app.get("/model-info")
def get_model_info():
    """Verification endpoint reporting loaded model metadata."""
    return get_model_metadata()


@app.post("/predict", response_model=PredictionResponse)
def predict_endpoint(payload: PredictionRequest):
    """
    Accepts 5 sensor readings, runs non-blocking range validation,
    runs model inference, and returns raw probability with any warnings.
    """
    warnings = validate_sensor_ranges(
        air_temperature=payload.air_temperature,
        process_temperature=payload.process_temperature,
        rotational_speed=payload.rotational_speed,
        torque=payload.torque,
        tool_wear=payload.tool_wear,
    )

    prob = predict_failure_probability(
        air_temperature=payload.air_temperature,
        process_temperature=payload.process_temperature,
        rotational_speed=payload.rotational_speed,
        torque=payload.torque,
        tool_wear=payload.tool_wear,
    )
    threshold = get_model_threshold()
    risk_level = get_risk_level(prob)

    return PredictionResponse(
        failure_probability=prob,
        threshold=threshold,
        failure_alert=prob >= threshold,
        risk_level=risk_level,
        maintenance_recommendation=get_maintenance_recommendation(risk_level),
        validation_warnings=warnings,
    )
