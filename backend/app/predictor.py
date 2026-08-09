"""
backend/app/predictor.py — Model Loader & Inference Engine

Loads the trained Random Forest artifact from models/rf_model.pkl
once at startup. Exposes metadata and raw probability inference functions.
"""

import os
import joblib
import pandas as pd

# Determine absolute path to models/rf_model.pkl relative to project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_PATH = os.path.join(BASE_DIR, "models", "rf_model.pkl")

_MODEL_ARTIFACT = None
_IS_LOADED = False


def _load_model():
    """Loads the model artifact once into module memory during initialization."""
    global _MODEL_ARTIFACT, _IS_LOADED

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model artifact not found at absolute path: '{MODEL_PATH}'. "
            "Ensure 'models/rf_model.pkl' exists by running 'python src/train_rf.py'."
        )

    try:
        _MODEL_ARTIFACT = joblib.load(MODEL_PATH)
        _IS_LOADED = True
    except Exception as e:
        raise RuntimeError(
            f"Failed to load model artifact from '{MODEL_PATH}': {str(e)}"
        )


# Load the model artifact once at startup when predictor.py is imported
_load_model()


def get_model_metadata() -> dict:
    """Returns basic metadata extracted from the loaded model artifact."""
    if not _IS_LOADED or _MODEL_ARTIFACT is None:
        return {"is_loaded": False, "error": "Model artifact is not loaded."}

    return {
        "is_loaded": _IS_LOADED,
        "target_name": _MODEL_ARTIFACT.get("target_name", "Machine failure"),
        "threshold": _MODEL_ARTIFACT.get("threshold", 0.5),
        "feature_names": _MODEL_ARTIFACT.get("feature_names", []),
        "feature_units": _MODEL_ARTIFACT.get("feature_units", {}),
        "feature_ranges": _MODEL_ARTIFACT.get("feature_ranges", {}),
    }


def get_model_threshold() -> float:
    """Returns the decision threshold stored in the loaded model artifact."""
    if not _IS_LOADED or _MODEL_ARTIFACT is None:
        raise RuntimeError("Cannot retrieve threshold: Model artifact is not loaded.")

    return float(_MODEL_ARTIFACT.get("threshold", 0.5))


def predict_failure_probability(
    air_temperature: float,
    process_temperature: float,
    rotational_speed: float,
    torque: float,
    tool_wear: float,
) -> float:
    """
    Accepts 5 raw sensor inputs, constructs a DataFrame matching model feature order,
    runs inference through the pipeline, and returns the raw failure probability (0.0 to 1.0).
    """
    if not _IS_LOADED or _MODEL_ARTIFACT is None:
        raise RuntimeError("Cannot perform inference: Model artifact is not loaded.")

    pipeline = _MODEL_ARTIFACT["pipeline"]
    feature_names = _MODEL_ARTIFACT.get(
        "feature_names",
        [
            "Air temperature [K]",
            "Process temperature [K]",
            "Rotational speed [rpm]",
            "Torque [Nm]",
            "Tool wear [min]",
        ],
    )

    # Format into DataFrame maintaining exact feature order expected by scikit-learn pipeline
    input_df = pd.DataFrame(
        [
            {
                "Air temperature [K]": air_temperature,
                "Process temperature [K]": process_temperature,
                "Rotational speed [rpm]": rotational_speed,
                "Torque [Nm]": torque,
                "Tool wear [min]": tool_wear,
            }
        ],
        columns=feature_names,
    )

    # Compute positive class probability (Machine failure = 1)
    probabilities = pipeline.predict_proba(input_df)
    failure_prob = float(probabilities[0][1])

    return failure_prob
