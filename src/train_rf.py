"""
src/train_rf.py — IronSight AI Phase 3: Random Forest & Threshold Tuning

This script trains a Random Forest model to predict machine failure from five sensor readings.
Random Forest is not scale-sensitive, so the pipeline contains ONLY the RandomForestClassifier.

Model selection and threshold selection follow a strict 7-step rule evaluated ONLY on training CV:
  1. Stratified 80/20 train-test split (random_state=42).
  2. 5-fold Stratified CV on training data to get out-of-fold predicted probabilities.
  3. Evaluate candidate thresholds (0.30, 0.40, 0.50, 0.60).
  4. Filter candidates keeping only those with CV Recall >= 0.80.
  5. Select candidate with highest CV F1-score (tie-breaker: higher CV Precision).
  6. Retrain winning Random Forest on all 8,000 training rows.
  7. Single final evaluation on unchanged 2,000-row test set.

Run from project root:
    .venv/bin/python src/train_rf.py
"""

import os
import json
import pandas as pd
import numpy as np
import joblib
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for saving plots
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_predict
from sklearn.ensemble import RandomForestClassifier
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
    # Step 1: Load data & Stratified 80/20 train-test split
    # ---------------------------------------------------------
    data_path = os.path.join("data", "ai4i2020.csv")
    print("=" * 60)
    print(f"Loading dataset from: {data_path}")
    print("=" * 60)

    df = pd.read_csv(data_path)
    
    feature_columns = [
        "Air temperature [K]",
        "Process temperature [K]",
        "Rotational speed [rpm]",
        "Torque [Nm]",
        "Tool wear [min]",
    ]
    target_column = "Machine failure"

    X = df[feature_columns]
    y = df[target_column]

    # Stratified 80/20 split (random_state=42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.20,
        stratify=y,
        random_state=42,
    )

    print(f"Training set: {X_train.shape[0]} rows")
    print(f"Test set:     {X_test.shape[0]} rows\n")

    # ---------------------------------------------------------
    # Compute feature min/max from TRAINING data only
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

    # ---------------------------------------------------------
    # Define 6 Random Forest configurations to evaluate
    # ---------------------------------------------------------
    rf_configs = [
        {"name": "RF-A", "n_estimators": 200, "max_depth": 10, "min_samples_leaf": 5},
        {"name": "RF-B", "n_estimators": 200, "max_depth": 15, "min_samples_leaf": 5},
        {"name": "RF-C", "n_estimators": 200, "max_depth": 20, "min_samples_leaf": 5},
        {"name": "RF-D", "n_estimators": 300, "max_depth": 10, "min_samples_leaf": 10},
        {"name": "RF-E", "n_estimators": 300, "max_depth": 15, "min_samples_leaf": 10},
        {"name": "RF-F", "n_estimators": 300, "max_depth": 20, "min_samples_leaf": 10},
    ]

    candidate_thresholds = [0.30, 0.40, 0.50, 0.60]

    # ---------------------------------------------------------
    # Step 2 & 3: Out-of-fold CV probabilities & threshold eval
    # ---------------------------------------------------------
    print("=" * 60)
    print("Evaluating RF configs & thresholds via 5-Fold Stratified CV on training data...")
    print("=" * 60)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    all_candidates = []

    for cfg in rf_configs:
        # Pipeline with ONLY RandomForestClassifier (no StandardScaler as RF is scale-invariant)
        model_pipeline = Pipeline([
            ("classifier", RandomForestClassifier(
                n_estimators=cfg["n_estimators"],
                max_depth=cfg["max_depth"],
                min_samples_leaf=cfg["min_samples_leaf"],
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            ))
        ])

        # Step 2: Get out-of-fold probability predictions on X_train
        oof_probs = cross_val_predict(
            model_pipeline, X_train, y_train, cv=cv, method="predict_proba"
        )[:, 1]

        # Step 3: Evaluate each candidate threshold
        for thresh in candidate_thresholds:
            oof_preds = (oof_probs >= thresh).astype(int)
            
            rec = recall_score(y_train, oof_preds, zero_division=0)
            prec = precision_score(y_train, oof_preds, zero_division=0)
            f1 = f1_score(y_train, oof_preds, zero_division=0)
            acc = accuracy_score(y_train, oof_preds)

            candidate_info = {
                "config_name": cfg["name"],
                "n_estimators": cfg["n_estimators"],
                "max_depth": cfg["max_depth"],
                "min_samples_leaf": cfg["min_samples_leaf"],
                "threshold": thresh,
                "cv_recall": rec,
                "cv_precision": prec,
                "cv_f1": f1,
                "cv_accuracy": acc,
            }
            all_candidates.append(candidate_info)

            print(f"[{cfg['name']}] Thresh: {thresh:.2f} | CV Recall: {rec:.4f} | CV Prec: {prec:.4f} | CV F1: {f1:.4f}")

    # ---------------------------------------------------------
    # Step 4: Filter candidates keeping only CV Recall >= 0.80
    # ---------------------------------------------------------
    eligible_candidates = [c for c in all_candidates if c["cv_recall"] >= 0.80]

    print("\n" + "=" * 60)
    print(f"Eligible Candidates (CV Recall >= 0.80): {len(eligible_candidates)} out of {len(all_candidates)}")
    print("=" * 60)

    if not eligible_candidates:
        print("Warning: No candidate met Recall >= 0.80! Falling back to all candidates.")
        eligible_candidates = all_candidates

    # ---------------------------------------------------------
    # Step 5: Select candidate with highest CV F1 (tie-breaker: precision)
    # ---------------------------------------------------------
    best_candidate = max(
        eligible_candidates,
        key=lambda x: (x["cv_f1"], x["cv_precision"])
    )

    print(f"\nWinning Model & Threshold Selected:")
    print(f"  Configuration: {best_candidate['config_name']} (n_estimators={best_candidate['n_estimators']}, max_depth={best_candidate['max_depth']}, min_samples_leaf={best_candidate['min_samples_leaf']})")
    print(f"  Threshold:     {best_candidate['threshold']:.2f}")
    print(f"  CV Recall:    {best_candidate['cv_recall']:.4f}")
    print(f"  CV Precision: {best_candidate['cv_precision']:.4f}")
    print(f"  CV F1-Score:  {best_candidate['cv_f1']:.4f}\n")

    # ---------------------------------------------------------
    # Step 6: Retrain winning Random Forest on full 8,000 training rows
    # ---------------------------------------------------------
    print("Retraining winning Random Forest on full 8,000-row training set...")
    final_pipeline = Pipeline([
        ("classifier", RandomForestClassifier(
            n_estimators=best_candidate["n_estimators"],
            max_depth=best_candidate["max_depth"],
            min_samples_leaf=best_candidate["min_samples_leaf"],
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        ))
    ])
    
    final_pipeline.fit(X_train, y_train)
    print("Retraining complete.\n")

    # ---------------------------------------------------------
    # Step 7: Single final evaluation on unchanged 2,000-row test set
    # ---------------------------------------------------------
    print("=" * 60)
    print("FINAL EVALUATION ON UNCHANGED 2,000-ROW TEST SET")
    print("=" * 60)

    test_probs = final_pipeline.predict_proba(X_test)[:, 1]
    best_thresh = best_candidate["threshold"]
    test_preds = (test_probs >= best_thresh).astype(int)

    test_acc = accuracy_score(y_test, test_preds)
    test_prec = precision_score(y_test, test_preds, zero_division=0)
    test_rec = recall_score(y_test, test_preds, zero_division=0)
    test_f1 = f1_score(y_test, test_preds, zero_division=0)
    test_cm = confusion_matrix(y_test, test_preds)

    print(f"Accuracy:  {test_acc:.4f}")
    print(f"Precision: {test_prec:.4f}")
    print(f"Recall:    {test_rec:.4f}")
    print(f"F1-Score:  {test_f1:.4f}")
    print("\nConfusion Matrix:")
    print(test_cm)
    print("\nFull Classification Report:")
    print(classification_report(y_test, test_preds, target_names=["No Failure", "Failure"]))

    # ---------------------------------------------------------
    # Step 8: Save Artifacts & Visualizations
    # ---------------------------------------------------------
    os.makedirs("models", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)

    # 8a. Save RF Model Artifact (includes threshold, feature names, units, training ranges)
    rf_artifact = {
        "pipeline": final_pipeline,
        "threshold": best_thresh,
        "feature_names": feature_columns,
        "feature_units": feature_units,
        "feature_ranges": feature_ranges,
        "target_name": target_column,
        "cv_selection_info": best_candidate,
    }
    rf_model_path = os.path.join("models", "rf_model.pkl")
    joblib.dump(rf_artifact, rf_model_path)
    print(f"Saved model artifact: {rf_model_path}")

    # 8b. Feature Importance Plot
    rf_model = final_pipeline.named_steps["classifier"]
    importances = rf_model.feature_importances_
    feat_imp_df = pd.DataFrame({
        "Feature": feature_columns,
        "Importance": importances
    }).sort_values(by="Importance", ascending=True)

    plt.figure(figsize=(8, 5))
    plt.barh(feat_imp_df["Feature"], feat_imp_df["Importance"], color="#2b5c8f")
    plt.title("Random Forest Feature Importances", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Importance Score", fontsize=11)
    plt.tight_layout()
    chart_imp_path = os.path.join("outputs", "rf_feature_importance.png")
    plt.savefig(chart_imp_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved chart: {chart_imp_path}")

    # 8c. Threshold Comparison Plot
    candidates_df = pd.DataFrame(all_candidates)
    winning_config_name = best_candidate["config_name"]
    winning_config_results = candidates_df[candidates_df["config_name"] == winning_config_name]

    plt.figure(figsize=(8, 5))
    plt.plot(winning_config_results["threshold"], winning_config_results["cv_recall"], marker="o", label="Recall", color="#d95f02", linewidth=2)
    plt.plot(winning_config_results["threshold"], winning_config_results["cv_precision"], marker="s", label="Precision", color="#2b5c8f", linewidth=2)
    plt.plot(winning_config_results["threshold"], winning_config_results["cv_f1"], marker="^", label="F1-Score", color="#7570b3", linewidth=2)
    plt.axvline(x=best_thresh, color="red", linestyle="--", label=f"Selected Thresh ({best_thresh:.2f})")
    plt.axhline(y=0.80, color="gray", linestyle=":", label="Recall Floor (0.80)")
    
    plt.title(f"CV Metrics across Thresholds ({winning_config_name})", fontsize=14, fontweight="bold", pad=12)
    plt.xlabel("Candidate Threshold", fontsize=11)
    plt.ylabel("Score", fontsize=11)
    plt.xticks(candidate_thresholds)
    plt.ylim(0, 1.05)
    plt.legend(loc="best")
    plt.tight_layout()
    chart_thresh_path = os.path.join("outputs", "rf_threshold_comparison.png")
    plt.savefig(chart_thresh_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved chart: {chart_thresh_path}")

    # 8d. Test Confusion Matrix Plot
    plt.figure(figsize=(6, 5))
    sns.heatmap(test_cm, annot=True, fmt="d", cmap="Greens",
                xticklabels=["No Failure", "Failure"],
                yticklabels=["No Failure", "Failure"])
    plt.title("Confusion Matrix — Random Forest", fontsize=12, fontweight="bold")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.tight_layout()
    chart_cm_path = os.path.join("outputs", "rf_confusion_matrix.png")
    plt.savefig(chart_cm_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Saved chart: {chart_cm_path}")

    # 8e. Classification Report Text File
    report_path = os.path.join("outputs", "rf_classification_report.txt")
    with open(report_path, "w") as f:
        f.write("IronSight AI — Random Forest Model (Phase 3)\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Selected Configuration: {best_candidate['config_name']}\n")
        f.write(f"Selected Threshold:     {best_thresh:.2f}\n\n")
        f.write(classification_report(y_test, test_preds, target_names=["No Failure", "Failure"]))
        f.write(f"\nAccuracy:  {test_acc:.4f}\n")
        f.write(f"Precision: {test_prec:.4f}\n")
        f.write(f"Recall:    {test_rec:.4f}\n")
        f.write(f"F1-Score:  {test_f1:.4f}\n")
    print(f"Saved classification report: {report_path}")

    # 8f. Metrics JSON File
    metrics_data = {
        "selected_config": best_candidate["config_name"],
        "selected_threshold": best_thresh,
        "accuracy": round(test_acc, 4),
        "precision": round(test_prec, 4),
        "recall": round(test_rec, 4),
        "f1_score": round(test_f1, 4),
        "confusion_matrix": {
            "true_negative": int(test_cm[0][0]),
            "false_positive": int(test_cm[0][1]),
            "false_negative": int(test_cm[1][0]),
            "true_positive": int(test_cm[1][1]),
        },
    }
    json_path = os.path.join("outputs", "rf_metrics.json")
    with open(json_path, "w") as f:
        json.dump(metrics_data, f, indent=2)
    print(f"Saved metrics JSON: {json_path}")

    # 8g. Model Comparison Text File
    lr_metrics_path = os.path.join("outputs", "baseline_metrics.json")
    lr_metrics = {}
    if os.path.exists(lr_metrics_path):
        with open(lr_metrics_path, "r") as f:
            lr_metrics = json.load(f)

    comp_path = os.path.join("outputs", "model_comparison.txt")
    with open(comp_path, "w") as f:
        f.write("IronSight AI — Model Performance Comparison\n")
        f.write("=" * 65 + "\n\n")
        f.write(f"{'Metric':<20} | {'Phase 2: Logistic Reg':<22} | {'Phase 3: Random Forest':<22}\n")
        f.write("-" * 65 + "\n")
        f.write(f"{'Threshold':<20} | {'0.50 (Default)':<22} | {best_thresh:<22.2f}\n")
        f.write(f"{'Accuracy':<20} | {lr_metrics.get('accuracy', 'N/A'):<22} | {test_acc:<22.4f}\n")
        f.write(f"{'Precision':<20} | {lr_metrics.get('precision', 'N/A'):<22} | {test_prec:<22.4f}\n")
        f.write(f"{'Recall':<20} | {lr_metrics.get('recall', 'N/A'):<22} | {test_rec:<22.4f}\n")
        f.write(f"{'F1-Score':<20} | {lr_metrics.get('f1_score', 'N/A'):<22} | {test_f1:<22.4f}\n")
        f.write("-" * 65 + "\n")
        lr_cm = lr_metrics.get("confusion_matrix", {})
        f.write(f"{'True Negatives (TN)':<20} | {lr_cm.get('true_negative', 'N/A'):<22} | {test_cm[0][0]:<22}\n")
        f.write(f"{'False Positives (FP)':<20} | {lr_cm.get('false_positive', 'N/A'):<22} | {test_cm[0][1]:<22}\n")
        f.write(f"{'False Negatives (FN)':<20} | {lr_cm.get('false_negative', 'N/A'):<22} | {test_cm[1][0]:<22}\n")
        f.write(f"{'True Positives (TP)':<20} | {lr_cm.get('true_positive', 'N/A'):<22} | {test_cm[1][1]:<22}\n")

    print(f"Saved side-by-side comparison: {comp_path}")

    print("\n" + "=" * 60)
    print("Phase 3 complete! All Random Forest outputs saved.")
    print("=" * 60)


if __name__ == "__main__":
    main()
