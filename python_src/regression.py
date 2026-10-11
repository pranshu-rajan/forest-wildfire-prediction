"""
Regression module: Forest Fires burned area prediction (Practical 9).

Dataset: Forest Fires (UCI ML Repository)
- Source: https://archive.ics.uci.edu/dataset/162/forest+fires
- Cortez, P. & Morais, A. (2007). A Data Mining Approach to Predict Forest Fires
  using Meteorological Data.
- Licence: CC BY 4.0

The Forest Fires task is completely SEPARATE from the Covertype classification.
The target variable is `area` (burned area in hectares), which is highly skewed
(many zero-area fires), so log1p transformation is commonly applied.

Regression models implemented:
- Linear Regression (baseline)
- Ridge Regression
- Decision Tree Regressor
- Random Forest Regressor

Evaluation metrics: MAE, RMSE, R²
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from python_src.logging_config import get_logger
from python_src.schemas import (
    FIRES_CATEGORICAL_FEATURES,
    FIRES_CONTINUOUS_FEATURES,
    FIRES_TARGET,
)

logger = get_logger(__name__)

FIRES_FILENAME = "forestfires.csv"
FIRES_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/forest-fires/forestfires.csv"


def check_fires_dataset(data_dir: Path) -> Path | None:
    """Check if the Forest Fires CSV exists in data/external."""
    path = data_dir / FIRES_FILENAME
    if path.exists():
        logger.info("Forest Fires dataset found at %s.", path)
        return path
    logger.warning(
        "Forest Fires dataset NOT found at %s.\n"
        "Download from: %s\n"
        "Place the file at: %s",
        path, FIRES_URL, path,
    )
    return None


def download_fires_dataset(data_dir: Path) -> Path | None:
    """Attempt to download the Forest Fires dataset from UCI."""
    import urllib.request
    path = data_dir / FIRES_FILENAME
    data_dir.mkdir(parents=True, exist_ok=True)
    try:
        logger.info("Downloading Forest Fires dataset from %s …", FIRES_URL)
        urllib.request.urlretrieve(FIRES_URL, path)
        logger.info("Download complete: %s", path)
        return path
    except Exception as exc:
        logger.warning("Download failed: %s. Manual download required.", exc)
        return None


def load_fires_dataset(path: Path) -> pd.DataFrame:
    """Load and preprocess the Forest Fires dataset."""
    df = pd.read_csv(path)
    logger.info("Loaded Forest Fires: %d rows × %d columns.", len(df), df.shape[1])

    # Encode categorical features
    le_month = LabelEncoder()
    le_day = LabelEncoder()
    df["month_enc"] = le_month.fit_transform(df["month"])
    df["day_enc"] = le_day.fit_transform(df["day"])

    return df


def prepare_fires_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return (X, y) for regression.

    y = log1p(area) due to strong right-skew and many zeros.
    """
    feature_cols = FIRES_CONTINUOUS_FEATURES + ["month_enc", "day_enc"]
    available_cols = [c for c in feature_cols if c in df.columns]
    X = df[available_cols].copy()
    y = np.log1p(df[FIRES_TARGET])
    return X, y


def get_regressors(random_state: int = 42) -> dict[str, Pipeline]:
    """Return regression pipelines."""
    return {
        "Linear Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("reg", LinearRegression()),
        ]),
        "Ridge Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("reg", Ridge(alpha=1.0)),
        ]),
        "Decision Tree": Pipeline([
            ("scaler", StandardScaler()),
            ("reg", DecisionTreeRegressor(max_depth=6, random_state=random_state)),
        ]),
        "Random Forest": Pipeline([
            ("scaler", StandardScaler()),
            ("reg", RandomForestRegressor(
                n_estimators=100, max_depth=10, n_jobs=-1, random_state=random_state
            )),
        ]),
    }


def evaluate_regressor(
    name: str,
    pipeline: Pipeline,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: np.ndarray,
    y_test: np.ndarray,
) -> dict[str, Any]:
    """Fit and evaluate a regressor. Returns metrics dict."""
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    # Also evaluate on original scale (expm1)
    y_test_orig = np.expm1(y_test)
    y_pred_orig = np.expm1(np.clip(y_pred, 0, None))
    mae_orig = float(mean_absolute_error(y_test_orig, y_pred_orig))
    rmse_orig = float(np.sqrt(mean_squared_error(y_test_orig, y_pred_orig)))

    result = {
        "model": name,
        "mae_log": round(mae, 4),
        "rmse_log": round(rmse, 4),
        "r2_log": round(r2, 4),
        "mae_original_scale": round(mae_orig, 4),
        "rmse_original_scale": round(rmse_orig, 4),
        "y_pred": y_pred.tolist(),
        "y_test": y_test.tolist(),
    }
    logger.info(
        "Regressor '%s': MAE=%.4f, RMSE=%.4f, R²=%.4f (log scale).",
        name, mae, rmse, r2,
    )
    return result


def run_fires_regression(
    data_dir: Path,
    out_dir: Path,
    random_state: int = 42,
    test_size: float = 0.20,
) -> dict[str, Any]:
    """Full Forest Fires regression pipeline."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Try to find or download the dataset
    fires_path = check_fires_dataset(data_dir)
    if fires_path is None:
        fires_path = download_fires_dataset(data_dir)
    if fires_path is None:
        return {
            "status": "DATASET_NOT_AVAILABLE",
            "message": (
                f"Forest Fires dataset not found. Download from {FIRES_URL} "
                f"and place at {data_dir / FIRES_FILENAME}"
            ),
        }

    df = load_fires_dataset(fires_path)
    X, y = prepare_fires_features(df)

    # Log-transform target distribution info
    n_zeros = int((df[FIRES_TARGET] == 0).sum())
    skewness = float(df[FIRES_TARGET].skew())
    logger.info(
        "Forest Fires target: n=%d, zeros=%d (%.1f%%), skewness=%.2f",
        len(df), n_zeros, n_zeros / len(df) * 100, skewness
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    regressors = get_regressors(random_state=random_state)
    all_results = []
    y_pred_dict = {}

    for name, pipeline in regressors.items():
        res = evaluate_regressor(name, pipeline, X_train, X_test, y_train, y_test)
        y_pred_dict[name] = res.pop("y_pred")
        y_test_arr = res.pop("y_test")
        all_results.append(res)

    # Build summary DataFrame
    metrics_df = pd.DataFrame(all_results)
    metrics_df.to_csv(out_dir / "forest_fires_regression_results.csv", index=False)

    # Save prediction results for best model (highest R²)
    best = metrics_df.sort_values("r2_log", ascending=False).iloc[0]
    best_name = best["model"]
    pred_df = pd.DataFrame({
        "y_true_log": y_test.values,
        "y_pred_log": y_pred_dict[best_name],
        "y_true_ha": np.expm1(y_test.values),
        "y_pred_ha": np.expm1(np.clip(y_pred_dict[best_name], 0, None)),
    })
    pred_df.to_csv(out_dir / "fires_best_model_predictions.csv", index=False)

    return_dict = {
        "status": "SUCCESS",
        "n_rows": len(df),
        "n_zeros_in_target": n_zeros,
        "target_skewness": round(skewness, 4),
        "target_transformation": "log1p",
        "models": all_results,
        "best_model": best_name,
    }

    with open(out_dir / "forest_fires_regression_summary.json", "w") as fh:
        json.dump(return_dict, fh, indent=2)

    return return_dict
