"""
Data cleaning module for the Covertype pipeline.

Philosophy
----------
- Outliers are **flagged**, never silently removed.
- Rows are only dropped when the **target** is missing (none expected).
- Every operation is recorded in a cleaning log with before/after counts.
- The original source CSV is never modified.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from python_src.logging_config import get_logger
from python_src.schemas import (
    CONTINUOUS_FEATURES,
    RECORD_ID_COLUMN,
    TARGET_COLUMN,
)

logger = get_logger(__name__)


@dataclass
class CleaningLog:
    """Records every cleaning operation applied to a DataFrame."""

    operations: list[dict[str, Any]] = field(default_factory=list)

    def record(
        self,
        operation: str,
        rows_in: int,
        rows_out: int,
        details: str = "",
    ) -> None:
        entry = {
            "operation": operation,
            "rows_in": rows_in,
            "rows_out": rows_out,
            "rows_affected": rows_in - rows_out,
            "details": details,
        }
        self.operations.append(entry)
        logger.info(
            "Cleaning op '%s': %d → %d rows (%+d). %s",
            operation,
            rows_in,
            rows_out,
            rows_out - rows_in,
            details,
        )

    def to_dict(self) -> dict[str, Any]:
        return {"operations": self.operations}

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        logger.info("Cleaning log saved to %s", path)


# ---------------------------------------------------------------------------
# Individual cleaning operations
# ---------------------------------------------------------------------------

def drop_missing_target(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    """Drop rows where Cover_Type is null (expected count: 0)."""
    n_in = len(df)
    mask = df[TARGET_COLUMN].isna()
    n_missing = int(mask.sum())
    df = df[~mask].copy()
    log.record(
        "drop_missing_target",
        n_in,
        len(df),
        f"Dropped {n_missing} rows with missing target.",
    )
    return df


def flag_iqr_outliers(
    df: pd.DataFrame,
    iqr_multiplier: float = 1.5,
) -> pd.DataFrame:
    """Add boolean flag columns '<col>_iqr_outlier' for each continuous feature.

    Rows are never deleted — only flagged for analytical awareness.
    """
    df = df.copy()
    for col in CONTINUOUS_FEATURES:
        if col not in df.columns:
            continue
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - iqr_multiplier * iqr
        upper = q3 + iqr_multiplier * iqr
        flag_col = f"{col}_iqr_outlier"
        df[flag_col] = ((df[col] < lower) | (df[col] > upper)).astype("int8")
    logger.info("IQR outlier flags added for %d continuous features.", len(CONTINUOUS_FEATURES))
    return df


def flag_zscore_outliers(
    df: pd.DataFrame,
    zscore_threshold: float = 3.0,
) -> pd.DataFrame:
    """Add boolean flag columns '<col>_zscore_outlier' for each continuous feature."""
    df = df.copy()
    for col in CONTINUOUS_FEATURES:
        if col not in df.columns:
            continue
        z = np.abs(stats.zscore(df[col].values, nan_policy="omit"))
        flag_col = f"{col}_zscore_outlier"
        df[flag_col] = (z > zscore_threshold).astype("int8")
    logger.info("Z-score outlier flags added for %d continuous features.", len(CONTINUOUS_FEATURES))
    return df


def build_outlier_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Return a summary DataFrame comparing IQR vs z-score outlier counts."""
    rows = []
    for col in CONTINUOUS_FEATURES:
        iqr_col = f"{col}_iqr_outlier"
        zscore_col = f"{col}_zscore_outlier"
        rows.append(
            {
                "feature": col,
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
                "iqr_outliers": int(df[iqr_col].sum()) if iqr_col in df.columns else None,
                "zscore_outliers": int(df[zscore_col].sum()) if zscore_col in df.columns else None,
            }
        )
    return pd.DataFrame(rows)


def clean_covtype(
    df: pd.DataFrame,
    iqr_multiplier: float = 1.5,
    zscore_threshold: float = 3.0,
) -> tuple[pd.DataFrame, CleaningLog]:
    """Apply the full cleaning pipeline to a loaded Covertype DataFrame.

    Steps:
    1. Drop rows with missing Cover_Type (expected 0).
    2. Flag IQR outliers on continuous features.
    3. Flag z-score outliers on continuous features.

    Returns the cleaned DataFrame and a CleaningLog.
    """
    log = CleaningLog()
    n_start = len(df)
    log.record("start", n_start, n_start, "Initial row count.")

    df = drop_missing_target(df, log)
    df = flag_iqr_outliers(df, iqr_multiplier=iqr_multiplier)
    df = flag_zscore_outliers(df, zscore_threshold=zscore_threshold)

    log.record("end", n_start, len(df), "Final row count after cleaning.")
    return df, log


def generate_quality_report(df: pd.DataFrame, label: str = "") -> pd.DataFrame:
    """Generate a per-column quality summary DataFrame."""
    rows = []
    for col in df.columns:
        if "_iqr_outlier" in col or "_zscore_outlier" in col:
            continue
        s = df[col]
        is_binary = s.isin([0, 1]).all() and s.nunique() <= 2
        rows.append(
            {
                "column": col,
                "label": label,
                "dtype": str(s.dtype),
                "n_missing": int(s.isna().sum()),
                "pct_missing": round(float(s.isna().mean() * 100), 4),
                "n_unique": int(s.nunique()),
                "is_binary": is_binary,
                "min": float(s.min()) if pd.api.types.is_numeric_dtype(s) else None,
                "max": float(s.max()) if pd.api.types.is_numeric_dtype(s) else None,
                "mean": float(s.mean()) if pd.api.types.is_numeric_dtype(s) else None,
            }
        )
    return pd.DataFrame(rows)
