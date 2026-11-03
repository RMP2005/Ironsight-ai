"""
src/evaluate.py — IronSight AI: evaluate saved artifacts on the locked test set.

Loads models/baseline_model.pkl and models/rf_model.pkl without retraining
and without writing to models/ or outputs/. Rebuilds the same stratified
80/20 split used in training (random_state=42) and scores the 2,000-row
test set with each model's saved decision rule:

  - baseline: pipeline.predict() (default 0.50 cutoff)
  - RF:       predict_proba >= saved threshold from the artifact

If the split does not reproduce a 2,000-row test set, the script stops
and reports why instead of printing numbers.

Run from project root:
    .venv/bin/python src/evaluate.py
"""

import json
import os
import sys

import joblib
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

FEATURE_COLUMNS = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
]
TARGET_COLUMN = "Machine failure"
EXPECTED_TEST_ROWS = 2000


def metrics_block(y_true, y_pred, label, threshold_note):
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = (int(cm[0][0]), int(cm[0][1]),
                      int(cm[1][0]), int(cm[1][1]))
    print(f"\n{label} ({threshold_note})")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1-Score:  {f1:.4f}")
    print(f"  Confusion: TN={tn} FP={fp} FN={fn} TP={tp}")
    return {
        "threshold": threshold_note,
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "true_positive": tp,
    }


def compare_with_stored(path, computed, name):
    if not os.path.exists(path):
        return
    with open(path) as f:
        stored = json.load(f)
    fields = ["accuracy", "precision", "recall", "f1_score"]
    cm = stored.get("confusion_matrix", {})
    stored_cm = [cm.get("true_negative"), cm.get("false_positive"),
                 cm.get("false_negative"), cm.get("true_positive")]
    computed_cm = [computed["true_negative"], computed["false_positive"],
                   computed["false_negative"], computed["true_positive"]]
    same = (
        all(abs(stored.get(k, -1) - computed[k]) < 1e-4 for k in fields)
        and stored_cm == computed_cm
    )
    status = "MATCHES" if same else "DIFFERS"
    print(f"\nReproducibility check vs {path} ({name}): {status}")
    if not same:
        print("  stored:   "
              f"{ {k: stored.get(k) for k in fields} } cm={stored_cm}")
        print("  computed: "
              f"{ {k: computed[k] for k in fields} } cm={computed_cm}")


def main():
    data_path = os.path.join("data", "ai4i2020.csv")
    if not os.path.exists(data_path):
        sys.exit(f"ABORT: dataset not found at {data_path}")

    df = pd.read_csv(data_path)
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # Same split as src/train.py and src/train_rf.py
    _, X_test, _, y_test = train_test_split(
        X, y,
        test_size=0.20,
        stratify=y,
        random_state=42,
    )

    if len(X_test) != EXPECTED_TEST_ROWS:
        sys.exit(
            "ABORT: split not reproducible — expected "
            f"{EXPECTED_TEST_ROWS} test rows, got {len(X_test)}. "
            "Check data/ai4i2020.csv and scikit-learn version."
        )

    print("=" * 62)
    print(f"Locked test set: {len(X_test)} rows "
          f"({int(y_test.sum())} failures, {int((y_test == 0).sum())} no-failure)")
    print("=" * 62)

    results = {}

    # --- Baseline (logistic regression, default 0.50 cutoff) ---
    baseline_path = os.path.join("models", "baseline_model.pkl")
    baseline = joblib.load(baseline_path)
    baseline_preds = baseline["pipeline"].predict(X_test)
    results["baseline"] = metrics_block(
        y_test, baseline_preds, "Baseline Logistic Regression",
        "threshold 0.50 (predict())",
    )
    compare_with_stored(
        os.path.join("outputs", "baseline_metrics.json"),
        results["baseline"], "baseline",
    )

    # --- Random Forest (saved threshold) ---
    rf_path = os.path.join("models", "rf_model.pkl")
    rf = joblib.load(rf_path)
    threshold = rf["threshold"]
    rf_probs = rf["pipeline"].predict_proba(X_test)[:, 1]
    rf_preds = (rf_probs >= threshold).astype(int)
    results["random_forest"] = metrics_block(
        y_test, rf_preds, "Random Forest (saved artifact)",
        f"threshold {threshold:.2f} (from artifact)",
    )
    compare_with_stored(
        os.path.join("outputs", "rf_metrics.json"),
        results["random_forest"], "random forest",
    )

    print("\n" + "=" * 62)
    print("Evaluation complete — no models or outputs were written.")
    print("=" * 62)


if __name__ == "__main__":
    main()
