"""
Data profiling module: generates detailed per-column and dataset-level profiles.

Covers Practical requirements for:
- Unit I: types of data, attribute types, sparse-data analysis
- Practical 3: descriptive statistics
- EDA: dataset summary, schema inspection, class distributions
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

from python_src.logging_config import get_logger
from python_src.schemas import (
    BINARY_FEATURES,
    CONTINUOUS_FEATURES,
    COVER_TYPE_NAMES,
    SOIL_FEATURES,
    TARGET_COLUMN,
    WILDERNESS_AREA_NAMES,
    WILDERNESS_FEATURES,
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Dataset-level profile
# ---------------------------------------------------------------------------

def dataset_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Return a comprehensive dataset-level summary dict."""
    n_rows, n_cols = df.shape
    n_missing_total = int(df.isna().sum().sum())
    n_duplicates = int(df.duplicated().sum())

    cont_cols = [c for c in CONTINUOUS_FEATURES if c in df.columns]
    bin_cols = [c for c in BINARY_FEATURES if c in df.columns]

    summary = {
        "n_rows": n_rows,
        "n_columns": n_cols,
        "n_continuous_features": len(cont_cols),
        "n_binary_features": len(bin_cols),
        "n_missing_total": n_missing_total,
        "pct_missing": round(n_missing_total / (n_rows * n_cols) * 100, 4),
        "n_duplicate_rows": n_duplicates,
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1e6, 2),
        "dtypes": {str(k): int(v) for k, v in df.dtypes.value_counts().items()},
        "columns": list(df.columns),
    }

    if TARGET_COLUMN in df.columns:
        dist = df[TARGET_COLUMN].value_counts().sort_index()
        summary["class_distribution"] = {
            int(k): {
                "count": int(v),
                "pct": round(v / n_rows * 100, 2),
                "name": COVER_TYPE_NAMES.get(int(k), "Unknown"),
            }
            for k, v in dist.items()
        }

    logger.info(
        "Dataset summary: %d rows, %d cols, %d missing, %d duplicates.",
        n_rows, n_cols, n_missing_total, n_duplicates,
    )
    return summary


# ---------------------------------------------------------------------------
# Descriptive statistics (Practical 3)
# ---------------------------------------------------------------------------

def descriptive_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute full descriptive statistics for all continuous features.

    Includes: mean, median, mode, midrange, min, max, range,
    Q1, Q3, IQR, variance, std dev, skewness, kurtosis.
    """
    cont_cols = [c for c in CONTINUOUS_FEATURES if c in df.columns]
    rows = []
    for col in cont_cols:
        s = df[col].dropna()
        q1 = float(s.quantile(0.25))
        q3 = float(s.quantile(0.75))
        mode_result = sp_stats.mode(s.values, keepdims=True)
        rows.append(
            {
                "feature": col,
                "count": int(s.count()),
                "mean": round(float(s.mean()), 4),
                "median": round(float(s.median()), 4),
                "mode": round(float(mode_result.mode[0]), 4),
                "midrange": round(float((s.min() + s.max()) / 2), 4),
                "min": float(s.min()),
                "max": float(s.max()),
                "range": float(s.max() - s.min()),
                "q1": round(q1, 4),
                "q3": round(q3, 4),
                "iqr": round(q3 - q1, 4),
                "variance": round(float(s.var()), 4),
                "std_dev": round(float(s.std()), 4),
                "skewness": round(float(s.skew()), 4),
                "kurtosis": round(float(s.kurtosis()), 4),
            }
        )
    df_stats = pd.DataFrame(rows)
    logger.info("Descriptive statistics computed for %d continuous features.", len(cont_cols))
    return df_stats


def five_number_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return the five-number summary (min, Q1, median, Q3, max) for continuous features."""
    cont_cols = [c for c in CONTINUOUS_FEATURES if c in df.columns]
    rows = []
    for col in cont_cols:
        s = df[col].dropna()
        rows.append(
            {
                "feature": col,
                "min": float(s.min()),
                "q1": float(s.quantile(0.25)),
                "median": float(s.median()),
                "q3": float(s.quantile(0.75)),
                "max": float(s.max()),
            }
        )
    return pd.DataFrame(rows)


def frequency_distributions(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Return value-count frequency distributions for binary and categorical features."""
    result: dict[str, pd.Series] = {}

    # Target class distribution
    if TARGET_COLUMN in df.columns:
        result["cover_type"] = df[TARGET_COLUMN].value_counts().sort_index()

    # Wilderness area frequencies
    for col in WILDERNESS_FEATURES:
        if col in df.columns:
            result[col] = df[col].value_counts().sort_index()

    # Soil type frequencies
    soil_activation = {}
    for col in SOIL_FEATURES:
        if col in df.columns:
            soil_activation[col] = int(df[col].sum())
    result["soil_type_activation_counts"] = pd.Series(soil_activation).sort_index()

    return result


# ---------------------------------------------------------------------------
# Per-column type classification
# ---------------------------------------------------------------------------

def classify_attribute_types(df: pd.DataFrame) -> pd.DataFrame:
    """Classify each column by data type category (continuous, binary, nominal, ordinal)."""
    rows = []
    for col in df.columns:
        s = df[col]
        n_unique = s.nunique()
        is_bin = s.isin([0, 1, np.nan]).all() and n_unique <= 2

        if col == TARGET_COLUMN:
            attr_type = "ordinal_nominal"
            description = "Target: Cover Type class (1–7, multiclass nominal)"
        elif col in CONTINUOUS_FEATURES:
            attr_type = "continuous_ratio" if col not in ("Aspect",) else "continuous_circular"
            description = "Continuous terrain/distance/hillshade measurement"
        elif is_bin:
            attr_type = "binary_nominal"
            description = "Binary one-hot indicator (0/1)"
        else:
            attr_type = "unknown"
            description = ""

        rows.append(
            {
                "column": col,
                "attribute_type": attr_type,
                "n_unique_values": int(n_unique),
                "description": description,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Wilderness and soil analysis
# ---------------------------------------------------------------------------

def wilderness_cover_crosstab(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-tabulation of Wilderness Area vs Cover Type counts."""
    # Decode one-hot to a single wilderness column
    wa_cols = [c for c in WILDERNESS_FEATURES if c in df.columns]
    if not wa_cols:
        return pd.DataFrame()
    df2 = df.copy()
    df2["wilderness_area"] = (
        df2[wa_cols]
        .idxmax(axis=1)
        .map(WILDERNESS_AREA_NAMES)
    )
    ct = pd.crosstab(df2["wilderness_area"], df2[TARGET_COLUMN])
    ct.columns = [COVER_TYPE_NAMES.get(c, str(c)) for c in ct.columns]
    return ct


def soil_type_frequency(df: pd.DataFrame) -> pd.DataFrame:
    """Return the activation frequency and proportion for each soil type."""
    soil_cols = [c for c in SOIL_FEATURES if c in df.columns]
    n = len(df)
    rows = [
        {
            "soil_type": col,
            "n_active": int(df[col].sum()),
            "pct_active": round(float(df[col].mean() * 100), 2),
        }
        for col in soil_cols
    ]
    return pd.DataFrame(rows).sort_values("n_active", ascending=False)


def classwise_continuous_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Mean of each continuous feature grouped by Cover_Type."""
    cont_cols = [c for c in CONTINUOUS_FEATURES if c in df.columns]
    if TARGET_COLUMN not in df.columns:
        return pd.DataFrame()
    grouped = df.groupby(TARGET_COLUMN)[cont_cols].mean().round(2)
    grouped.index = [COVER_TYPE_NAMES.get(i, str(i)) for i in grouped.index]
    return grouped
