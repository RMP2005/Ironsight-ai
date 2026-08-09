# IronSight AI — Predictive Maintenance

An end-to-end machine learning project that predicts industrial machine failures from real-time sensor data.

## Project Structure

```
ironsight-ai/
├── data/
│   └── ai4i2020.csv                      # Source dataset (read-only, never modified)
├── models/
│   ├── baseline_model.pkl                 # Logistic Regression artifact (Phase 2)
│   └── rf_model.pkl                       # Random Forest artifact + threshold (Phase 3)
├── outputs/
│   ├── failure_distribution.png           # Chart: Failure class imbalance (Phase 1)
│   ├── tool_wear_vs_failure.png           # Chart: Tool wear comparison (Phase 1)
│   ├── torque_vs_failure.png              # Chart: Torque comparison (Phase 1)
│   ├── sensor_correlation_heatmap.png     # Chart: Feature correlations (Phase 1)
│   ├── confusion_matrix.png              # Chart: Baseline confusion matrix (Phase 2)
│   ├── classification_report.txt          # Text: Baseline evaluation report (Phase 2)
│   ├── baseline_metrics.json             # JSON:  Baseline metrics (Phase 2)
│   ├── rf_feature_importance.png         # Chart: RF feature importances (Phase 3)
│   ├── rf_threshold_comparison.png       # Chart: RF CV metrics across thresholds (Phase 3)
│   ├── rf_confusion_matrix.png           # Chart: RF test confusion matrix (Phase 3)
│   ├── rf_classification_report.txt     # Text: RF test evaluation report (Phase 3)
│   ├── rf_metrics.json                    # JSON:  RF test metrics (Phase 3)
│   └── model_comparison.txt              # Text: Baseline vs RF test comparison (Phase 3)
├── src/
│   ├── train.py                           # Baseline Logistic Regression script (Phase 2)
│   └── train_rf.py                        # Random Forest & Threshold tuning script (Phase 3)
├── analysis.py                            # Exploratory data analysis script (Phase 1)
├── requirements.txt                       # Python dependencies
└── README.md                              # This file
```

## Selected Sensor Features

| # | Feature                    | Unit |
|---|----------------------------|------|
| 1 | Air temperature [K]        | K    |
| 2 | Process temperature [K]    | K    |
| 3 | Rotational speed [rpm]     | rpm  |
| 4 | Torque [Nm]                | Nm   |
| 5 | Tool wear [min]            | min  |

**Target Variable:** `Machine failure` (0 = No Failure, 1 = Failure)

---

## Setup & Installation

### 1. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 2. Phase 1 — Exploratory Data Analysis

Generate dataset summary statistics and four sensor visualisation charts:

```bash
.venv/bin/python analysis.py
```

### 3. Phase 2 — Train Baseline Model (Logistic Regression)

Train a Logistic Regression classifier with balanced class weights:

```bash
.venv/bin/python src/train.py
```

Outputs are saved in `models/baseline_model.pkl` and `outputs/`.

### 4. Phase 3 — Train Random Forest & Threshold Tuning

Train a Random Forest classifier with CV-based threshold selection:

```bash
.venv/bin/python src/train_rf.py
```

This script executes the approved 7-step model selection rule:
1. Stratified 80/20 train-test split (`random_state=42`).
2. 5-Fold Stratified CV on training data to generate out-of-fold probability predictions.
3. Evaluates candidate thresholds (`0.30`, `0.40`, `0.50`, `0.60`).
4. Filters candidates to enforce **CV Recall ≥ 0.80**.
5. Selects candidate with highest CV F1-Score (tie-breaker: higher CV Precision).
6. Retrains the winning Random Forest configuration on the full 8,000-row training set.
7. Evaluates the locked model and threshold **exactly once** on the 2,000-row test set.

---

## Model Artifact Contents

The saved file `models/rf_model.pkl` contains:

| Key              | Description                                                             |
|------------------|-------------------------------------------------------------------------|
| `pipeline`       | Scikit-learn Pipeline (`RandomForestClassifier` only)                   |
| `threshold`      | Optimal probability decision threshold selected from training CV        |
| `feature_names`  | List of the 5 input feature column names                                |
| `feature_units`  | Dict of feature units (`K`, `rpm`, `Nm`, `min`)                        |
| `feature_ranges` | Min, max, and unit for each feature (training data only)                |
| `target_name`    | Name of the prediction target column (`Machine failure`)                |

---

## Deployment (Render backend + Vercel frontend)

This project is intended to deploy as:

- **Backend:** Render (FastAPI / Uvicorn), repository root as the service root
- **Frontend:** Vercel (Next.js app in `frontend/`)

### Recommended Python (Render)

Use **Python 3.14.3** (see `.python-version`). Backend ML pins in `backend/requirements.txt` were verified against this runtime and the existing `models/rf_model.pkl`.

### Render build / start

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

### Backend environment variables

```bash
CORS_ORIGINS=https://your-vercel-app.vercel.app
```

- Comma-separated exact origins are supported (no `*`).
- Local default (when unset): `http://localhost:3000`

Optional (if not relying on `.python-version`):

```bash
PYTHON_VERSION=3.14.3
```

### Frontend environment variables (Vercel)

Root Directory: `frontend`

```bash
NEXT_PUBLIC_API_BASE_URL=https://your-render-service.onrender.com
```

Do not commit real production URLs or `.env.local` secrets.
