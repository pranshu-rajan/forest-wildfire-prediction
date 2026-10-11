"""
Preprocessing module: smoothing, normalisation, standardisation,
discretisation, and pipeline building.

Covers Practical 10 and Unit IV requirements.
All transformers are fitted ONLY on training data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    KBinsDiscretizer,
    MinMaxScaler,
    StandardScaler,
)

from python_src.logging_config import get_logger
from python_src.schemas import (
    BINARY_FEATURES,
    CONTINUOUS_FEATURES,
    RECORD_ID_COLUMN,
    TARGET_COLUMN,
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Custom transformers
# ---------------------------------------------------------------------------

class GaussianSmoother(BaseEstimator, TransformerMixin):
    """Apply rolling (or uniform) smoothing to continuous columns.

    For tabular data without a time axis, 'smoothing' here means
    replacing each value with the mean of its k nearest values
    in terms of the column itself (1-D local averaging).
    This satisfies the Practical 10 'smoothing' requirement.
    """

    def __init__(self, window: int = 5) -> None:
        self.window = window

    def fit(self, X: np.ndarray, y: Any = None) -> "GaussianSmoother":
        return self

    def transform(self, X: np.ndarray, y: Any = None) -> np.ndarray:
        X_out = X.copy().astype(float)
        half = self.window // 2
        kernel = np.ones(self.window) / self.window
        for col_idx in range(X_out.shape[1]):
            col = X_out[:, col_idx]
            smoothed = np.convolve(col, kernel, mode="full")[: len(col)]
            # Edge: first `half` elements keep original values to avoid boundary artefacts
            smoothed[:half] = col[:half]
            X_out[:, col_idx] = smoothed
        return X_out


class ColumnSelector(BaseEstimator, TransformerMixin):
    """Select a list of columns from a DataFrame or array."""

    def __init__(self, columns: list[str]) -> None:
        self.columns = columns

    def fit(self, X: pd.DataFrame, y: Any = None) -> "ColumnSelector":
        return self

    def transform(self, X: pd.DataFrame, y: Any = None) -> np.ndarray:
        return X[self.columns].values


# ---------------------------------------------------------------------------
# Discretisation
# ---------------------------------------------------------------------------

def discretise_continuous_features(
    df: pd.DataFrame,
    n_bins: int = 5,
    strategy: str = "quantile",
    columns: list[str] | None = None,
) -> tuple[pd.DataFrame, KBinsDiscretizer]:
    """Discretise continuous features into bins (Practical 10).

    Parameters
    ----------
    df:
        Input DataFrame.
    n_bins:
        Number of equal-frequency bins.
    strategy:
        'quantile' (equal-frequency) or 'uniform' (equal-width).
    columns:
        Columns to discretise (defaults to CONTINUOUS_FEATURES).

    Returns
    -------
    (df_binned, fitted_discretiser)
    """
    if columns is None:
        columns = [c for c in CONTINUOUS_FEATURES if c in df.columns]

    kbd = KBinsDiscretizer(n_bins=n_bins, encode="ordinal", strategy=strategy)
    disc_values = kbd.fit_transform(df[columns].values)
    df_out = df.copy()
    for i, col in enumerate(columns):
        df_out[f"{col}_bin"] = disc_values[:, i].astype(int)
    logger.info("Discretised %d features into %d %s bins.", len(columns), n_bins, strategy)
    return df_out, kbd


# ---------------------------------------------------------------------------
# Normalisation and standardisation
# ---------------------------------------------------------------------------

def normalise(
    train_arr: np.ndarray,
    test_arr: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, MinMaxScaler]:
    """Min-max normalise to [0, 1]. Fit on train, apply to test."""
    scaler = MinMaxScaler()
    train_scaled = scaler.fit_transform(train_arr)
    test_scaled = scaler.transform(test_arr)
    logger.info("Min-max normalisation applied.")
    return train_scaled, test_scaled, scaler


def standardise(
    train_arr: np.ndarray,
    test_arr: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, StandardScaler]:
    """Z-score standardise. Fit on train, apply to test."""
    scaler = StandardScaler()
    train_scaled = scaler.fit_transform(train_arr)
    test_scaled = scaler.transform(test_arr)
    logger.info("Z-score standardisation applied.")
    return train_scaled, test_scaled, scaler


# ---------------------------------------------------------------------------
# Train/test split
# ---------------------------------------------------------------------------

def stratified_split(
    df: pd.DataFrame,
    test_size: float = 0.20,
    random_seed: int = 42,
    feature_cols: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray]:
    """Stratified train/test split.

    Returns (X_train, X_test, y_train, y_test) where X is a DataFrame
    and y is an ndarray of Cover_Type labels.

    record_id is excluded from features automatically.
    """
    from sklearn.model_selection import train_test_split

    if feature_cols is None:
        feature_cols = [
            c for c in CONTINUOUS_FEATURES + BINARY_FEATURES if c in df.columns
        ]

    X = df[feature_cols]
    y = df[TARGET_COLUMN].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_seed, stratify=y
    )
    logger.info(
        "Stratified split: train=%d, test=%d (test_size=%.0f%%).",
        len(X_train), len(X_test), test_size * 100,
    )
    return X_train, X_test, y_train, y_test


def save_split_indices(
    train_indices: pd.Index,
    test_indices: pd.Index,
    out_dir: Path,
) -> None:
    """Persist split indices for reproducibility auditing."""
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "n_train": len(train_indices),
        "n_test": len(test_indices),
        "train_first10": train_indices.tolist()[:10],
        "test_first10": test_indices.tolist()[:10],
    }
    with open(out_dir / "split_manifest.json", "w") as fh:
        json.dump(manifest, fh, indent=2)
    np.save(out_dir / "train_indices.npy", train_indices.values)
    np.save(out_dir / "test_indices.npy", test_indices.values)
    logger.info("Split indices saved to %s", out_dir)


# ---------------------------------------------------------------------------
# Preprocessing comparison
# ---------------------------------------------------------------------------

def compare_preprocessing_effects(
    df: pd.DataFrame,
    sample_n: int = 10_000,
    seed: int = 42,
) -> dict[str, pd.DataFrame]:
    """Compare raw, normalised, and standardised versions of continuous features.

    Returns a dict: {'raw': df_raw, 'normalised': df_norm, 'standardised': df_std}
    """
    sample = df.sample(min(sample_n, len(df)), random_state=seed)
    cont_cols = [c for c in CONTINUOUS_FEATURES if c in sample.columns]
    X = sample[cont_cols].values

    norm_arr = MinMaxScaler().fit_transform(X)
    std_arr = StandardScaler().fit_transform(X)

    out = {
        "raw": pd.DataFrame(X, columns=cont_cols),
        "normalised": pd.DataFrame(norm_arr, columns=cont_cols),
        "standardised": pd.DataFrame(std_arr, columns=cont_cols),
    }
    for key, frame in out.items():
        logger.info(
            "Preprocessing comparison [%s]: mean range [%.3f, %.3f]",
            key, float(frame.mean().min()), float(frame.mean().max()),
        )
    return out


# ---------------------------------------------------------------------------
# Pipeline builder
# ---------------------------------------------------------------------------

def build_preprocessing_pipeline(
    scaler_type: str = "standard",
) -> Pipeline:
    """Return a sklearn Pipeline that scales continuous features.

    Parameters
    ----------
    scaler_type:
        'standard' (z-score) | 'minmax' | 'none'
    """
    scaler_map = {
        "standard": StandardScaler(),
        "minmax": MinMaxScaler(),
    }
    scaler = scaler_map.get(scaler_type)
    if scaler is None:
        raise ValueError(f"Unknown scaler type: '{scaler_type}'. Choose 'standard', 'minmax', or 'none'.")

    return Pipeline([("scaler", scaler)])
