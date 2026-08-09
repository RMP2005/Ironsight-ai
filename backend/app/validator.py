"""
backend/app/validator.py — Domain & Input Range Validator

Validates incoming sensor inputs against training feature ranges loaded from
the model artifact. Generates non-blocking warnings if values lie outside
the range seen during training.
"""

from backend.app.predictor import get_model_metadata


# Map between Pydantic request field names and model artifact feature names
FIELD_TO_FEATURE_MAP = {
    "air_temperature": "Air temperature [K]",
    "process_temperature": "Process temperature [K]",
    "rotational_speed": "Rotational speed [rpm]",
    "torque": "Torque [Nm]",
    "tool_wear": "Tool wear [min]",
}


def validate_sensor_ranges(
    air_temperature: float,
    process_temperature: float,
    rotational_speed: float,
    torque: float,
    tool_wear: float,
) -> list[str]:
    """
    Compares incoming sensor values against stored min/max feature ranges.
    Returns a list of human-readable warning strings for any out-of-range values.
    Returns an empty list if all values are within bounds.
    """
    metadata = get_model_metadata()
    feature_ranges = metadata.get("feature_ranges", {})

    warnings = []

    input_values = {
        "air_temperature": air_temperature,
        "process_temperature": process_temperature,
        "rotational_speed": rotational_speed,
        "torque": torque,
        "tool_wear": tool_wear,
    }

    for field_name, feature_name in FIELD_TO_FEATURE_MAP.items():
        val = input_values[field_name]
        range_info = feature_ranges.get(feature_name)

        if range_info and ("min" in range_info) and ("max" in range_info):
            min_val = range_info["min"]
            max_val = range_info["max"]
            unit = range_info.get("unit", "")

            if val < min_val or val > max_val:
                unit_str = f" {unit}".rstrip() if unit else ""
                warnings.append(
                    f"{feature_name} value ({val}{unit_str}) is outside the training range "
                    f"({min_val}–{max_val}{unit_str}). Prediction may be less reliable."
                )

    return warnings
