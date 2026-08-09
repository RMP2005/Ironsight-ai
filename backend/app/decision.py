"""Application-level decision-support recommendation logic."""


def get_maintenance_recommendation(risk_level: str) -> str:
    """Returns a deterministic decision-support recommendation for a risk level."""
    recommendations = {
        "Low": "Continue routine monitoring; no immediate maintenance action is indicated by the model.",
        "Moderate": "Consider scheduling a routine inspection and continue monitoring operating conditions.",
        "High": "Prioritize engineering inspection and review recent operating conditions before continued operation.",
    }
    return recommendations[risk_level]
