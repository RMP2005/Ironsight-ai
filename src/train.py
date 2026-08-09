"""
src/train.py — IronSight AI Phase 2: Baseline Model Training

This script trains a Logistic Regression model to predict machine failure
from five sensor readings. It uses a scikit-learn Pipeline to bundle
feature scaling and the classifier into a single object, preventing
data leakage.

Run from the project root:
    .venv/bin/python src/train.py
"""

import os
import json
import pandas as pd
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")  # Use non-interactive backend for saving plots
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)


def main():
    # ---------------------------------------------------------
    # Step 1: Load the dataset (read-only — never modified)
    # ---------------------------------------------------------
    data_path = os.path.join("data", "ai4i2020.csv")
    print("=" * 60)
    print(f"Loading dataset from: {data_path}")
    print("=" * 60)

    df = pd.read_csv(data_path)
    print(f"Dataset shape: {df.shape[0]} rows, {df.shape[1]} columns\n")

    # ---------------------------------------------------------
    # Step 2: Select the five sensor features and the target
    # ---------------------------------------------------------
    feature_columns = [
        "Air temperature [K]",
        "Process temperature [K]",
        "Rotational speed [rpm]",
        "Torque [Nm]",
        "Tool wear [min]",
    ]
    target_column = "Machine failure"

    X = df[feature_columns]  # Sensor inputs (10000 x 5)
    y = df[target_column]    # Binary target (10000 x 1)

    print(f"Features: {feature_columns}")
    print(f"Target:   {target_column}")
    print(f"Failure rate: {y.mean() * 100:.2f}%\n")

    # ---------------------------------------------------------
    # Step 3: Stratified 80/20 train-test split
    #
    #   stratify=y  → keeps the ~3.39% failure ratio in both
    #                  the training set and the test set
    #   random_state=42 → makes the split repeatable
    # ---------------------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.20,
        stratify=y,
        random_state=42,
    )

    print(f"Training set: {X_train.shape[0]} rows")
    print(f"Test set:     {X_test.shape[0]} rows\n")

    # ---------------------------------------------------------
    # Step 4: Compute feature min / max from TRAINING data only
    #         (saved later for website input-range validation)
    #
    #   Why X_train only?  Any statistic we save — even simple
    #   min/max — must come from training data so no information
    #   about the test set leaks into the model artifact.
    # ---------------------------------------------------------
    feature_units = {
        "Air temperature [K]": "K",
        "Process temperature [K]": "K",
        "Rotational speed [rpm]": "rpm",
        "Torque [Nm]": "Nm",
        "Tool wear [min]": "min",
    }

    feature_ranges = {}
    for col in feature_columns:
        feature_ranges[col] = {
            "min": float(X_train[col].min()),
            "max": float(X_train[col].max()),
            "unit": feature_units[col],
        }

    print("Feature ranges (training set only):")
    for col, info in feature_ranges.items():
        print(f"  {col}: {info['min']} – {info['max']} {info['unit']}")
    print()

    # ---------------------------------------------------------
    # Step 5: Build a scikit-learn Pipeline
    #
    #   The Pipeline bundles two steps together:
    #     1. StandardScaler — normalises each sensor column
    #        so values have mean=0 and std=1.
    #     2. LogisticRegression — the classifier itself.
    #
    #   Why a Pipeline?  It guarantees that the scaler is
    #   fitted ONLY on training data, preventing data leakage.
    #   When we call pipeline.fit(X_train, y_train), the scaler
    #   learns from X_train and the model trains on scaled
    #   X_train.  When we call pipeline.predict(X_test), the
    #   scaler applies the TRAINING statistics to X_test.
    # ---------------------------------------------------------
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            class_weight="balanced",   # Adjusts for the 96.6% / 3.4% imbalance
            random_state=42,
            max_iter=1000,             # Ensure convergence
        )),
    ])

    print("Training Logistic Regression (class_weight='balanced')...")
    pipeline.fit(X_train, y_train)
    print("Training complete.\n")

    # ---------------------------------------------------------
    # Step 6: Evaluate on the held-out test set
    # ---------------------------------------------------------
    y_pred = pipeline.predict(X_test)

    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec  = recall_score(y_test, y_pred, zero_division=0)
    f1   = f1_score(y_test, y_pred, zero_division=0)
    cm   = confusion_matrix(y_test, y_pred)

    print("=" * 60)
    print("TEST SET EVALUATION")
    print("=" * 60)
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1-Score:  {f1:.4f}")
    print()
    print("Confusion Matrix:")
    print(cm)
    print()
    print("Full Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["No Failure", "Failure"]))

    # ---------------------------------------------------------
    # Step 7: Save outputs
    # ---------------------------------------------------------
    # Ensure output directories exist
    os.makedirs("models", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)

    # --- 7a. Save the model artifact ---
    #     Includes the pipeline, feature names, units, and
    #     min/max ranges for website input validation later.
    model_artifact = {
        "pipeline": pipeline,
        "feature_names": feature_columns,
        "feature_ranges": feature_ranges,
        "target_name": target_column,
    }

    model_path = os.path.join("models", "baseline_model.pkl")
    joblib.dump(model_artifact, model_path)
    print(f"Model saved to: {model_path}")

    # --- 7b. Save confusion matrix chart ---
    plt.figure(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["No Failure", "Failure"],
        yticklabels=["No Failure", "Failure"],
    )
    plt.title("Confusion Matrix — Baseline Logistic Regression", fontsize=12, fontweight="bold")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.tight_layout()

    cm_path = os.path.join("outputs", "confusion_matrix.png")
    plt.savefig(cm_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Confusion matrix chart saved to: {cm_path}")

    # --- 7c. Save classification report text ---
    report_path = os.path.join("outputs", "classification_report.txt")
    with open(report_path, "w") as f:
        f.write("IronSight AI — Baseline Logistic Regression\n")
        f.write("=" * 50 + "\n\n")
        f.write(classification_report(y_test, y_pred, target_names=["No Failure", "Failure"]))
        f.write(f"\nAccuracy:  {acc:.4f}\n")
        f.write(f"Precision: {prec:.4f}\n")
        f.write(f"Recall:    {rec:.4f}\n")
        f.write(f"F1-Score:  {f1:.4f}\n")
    print(f"Classification report saved to: {report_path}")

    # --- 7d. Save metrics as JSON (for programmatic use) ---
    metrics = {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": {
            "true_negative": int(cm[0][0]),
            "false_positive": int(cm[0][1]),
            "false_negative": int(cm[1][0]),
            "true_positive": int(cm[1][1]),
        },
    }

    metrics_path = os.path.join("outputs", "baseline_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics JSON saved to: {metrics_path}")

    print("\n" + "=" * 60)
    print("Phase 2 complete! All outputs saved.")
    print("=" * 60)


if __name__ == "__main__":
    main()
