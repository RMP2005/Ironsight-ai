"""
backend/app/schemas.py — Pydantic Schemas for Prediction API

Defines data validation models for API requests and responses.
"""

from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Input payload for raw sensor measurements."""

    air_temperature: float = Field(
        ..., description="Air temperature in Kelvin [K]", example=298.1
    )
    process_temperature: float = Field(
        ..., description="Process temperature in Kelvin [K]", example=308.6
    )
    rotational_speed: float = Field(
        ..., description="Rotational speed in RPM [rpm]", example=1551.0
    )
    torque: float = Field(
        ..., description="Torque in Newton-meters [Nm]", example=42.8
    )
    tool_wear: float = Field(
        ..., description="Tool wear time in minutes [min]", example=0.0
    )


class PredictionResponse(BaseModel):
    """Output payload containing probability, alert, risk, recommendation, and warnings."""

    failure_probability: float = Field(
        ...,
        description="Predicted probability of machine failure (0.0 to 1.0)",
        example=0.034,
    )
    threshold: float = Field(
        ...,
        description="Failure-alert decision threshold stored in the model artifact",
    )
    failure_alert: bool = Field(
        ...,
        description="True when failure probability is greater than or equal to the threshold",
        example=False,
    )
    risk_level: str = Field(
        ...,
        description="Prototype application-level risk classification based on failure probability",
        example="Low",
    )
    maintenance_recommendation: str = Field(
        ...,
        description="Deterministic decision-support recommendation based only on risk level",
    )
    validation_warnings: list[str] = Field(
        default_factory=list,
        description="List of non-blocking warnings for out-of-range inputs",
        example=[],
    )
