"""
Statistics module: correlation, chi-square, and frequency analysis.

Covers Practical 10 requirements:
- Pearson correlation
- Chi-square feature selection/testing
- Redundancy analysis
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as sp_stats
from sklearn.feature_selection import chi2
from sklearn.preprocessing import MinMaxScaler

from python_src.logging_config import get_logger
from python_src.schemas import (
    BINARY_FEATURES,
    CONTINUOUS_FEATURES,
    TARGET_COLUMN,
)

logger = get_logger(__name__)


def pearson_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Compute Pearson correlation matrix for continuous features only."""
    cont_cols = [c for c in CONTINUOUS_FEATURES if c in df.columns]
    corr = df[cont_cols].corr(method="pearson")
    logger.info("Pearson correlation matrix computed (%dx%d).", len(cont_cols), len(cont_cols))
    return corr


def high_correlations(
    corr_matrix: pd.DataFrame,
    threshold: float = 0.75,
) -> pd.DataFrame:
    """Return pairs of features with |correlation| > threshold."""
    rows = []
    cols = corr_matrix.columns.tolist()
    for i, c1 in enumerate(cols):
        for c2 in cols[i + 1 :]:
            r = float(corr_matrix.loc[c1, c2])
            if abs(r) > threshold:
                rows.append({"feature_a": c1, "feature_b": c2, "pearson_r": round(r, 4)})
    if not rows:
        return pd.DataFrame(columns=["feature_a", "feature_b", "pearson_r"])
    df_pairs = pd.DataFrame(rows).sort_values("pearson_r", key=abs, ascending=False)
    logger.info("Found %d feature pairs with |r| > %.2f.", len(df_pairs), threshold)
    return df_pairs


def chi2_feature_scores(
    df: pd.DataFrame,
    sample_n: int | None = 50_000,
    seed: int = 42,
) -> pd.DataFrame:
    """Compute chi-square scores between features and Cover_Type.

    Chi-square requires non-negative feature values.
    - Continuous features are min-max scaled to [0, 1] first.
    - Binary features (0/1) are already non-negative.

    Returns a DataFrame sorted by chi2 score descending.
    """
    work = df.copy()
    if sample_n and len(work) > sample_n:
        work = work.sample(n=sample_n, random_state=seed)
        logger.info("Chi-square test using %d-row sample.", sample_n)

    all_feature_cols = [c for c in (CONTINUOUS_FEATURES + BINARY_FEATURES) if c in work.columns]
    X = work[all_feature_cols].fillna(0).copy()

    # Scale continuous to [0,1] for chi2 non-negativity requirement
    cont_in_X = [c for c in CONTINUOUS_FEATURES if c in X.columns]
    scaler = MinMaxScaler()
    X[cont_in_X] = scaler.fit_transform(X[cont_in_X])

    y = work[TARGET_COLUMN].values
    scores, pvalues = chi2(X.values, y)

    result = pd.DataFrame(
        {
            "feature": all_feature_cols,
            "chi2_score": scores.round(4),
            "p_value": pvalues.round(6),
            "is_significant_0.05": pvalues < 0.05,
        }
    ).sort_values("chi2_score", ascending=False)

    logger.info("Chi-square scores computed for %d features.", len(all_feature_cols))
    return result


def redundancy_analysis(
    corr_matrix: pd.DataFrame,
    threshold: float = 0.90,
) -> list[str]:
    """Identify redundant features using greedy correlation-based elimination.

    Returns a list of feature names recommended for removal.
    """
    to_drop: set[str] = set()
    cols = corr_matrix.columns.tolist()
    for i, c1 in enumerate(cols):
        if c1 in to_drop:
            continue
        for c2 in cols[i + 1 :]:
            if c2 in to_drop:
                continue
            if abs(corr_matrix.loc[c1, c2]) >= threshold:
                to_drop.add(c2)
    logger.info(
        "Redundancy analysis: %d features recommended for removal at r >= %.2f.",
        len(to_drop), threshold,
    )
    return sorted(to_drop)


def point_biserial_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """Compute point-biserial correlations between Cover_Type and binary features."""
    rows = []
    for col in BINARY_FEATURES:
        if col not in df.columns:
            continue
        r, p = sp_stats.pointbiserialr(df[col].values, df[TARGET_COLUMN].values)
        rows.append({"feature": col, "pb_r": round(r, 4), "p_value": round(p, 6)})
    return pd.DataFrame(rows).sort_values("pb_r", key=abs, ascending=False)


def anova_f_scores(df: pd.DataFrame, sample_n: int | None = 50_000, seed: int = 42) -> pd.DataFrame:
    """ANOVA F-scores between each continuous feature and Cover_Type (as groups)."""
    from sklearn.feature_selection import f_classif
    work = df.copy()
    if sample_n and len(work) > sample_n:
        work = work.sample(n=sample_n, random_state=seed)

    cont_cols = [c for c in CONTINUOUS_FEATURES if c in work.columns]
    X = work[cont_cols].values
    y = work[TARGET_COLUMN].values
    scores, pvalues = f_classif(X, y)
    result = pd.DataFrame(
        {
            "feature": cont_cols,
            "f_score": scores.round(4),
            "p_value": pvalues.round(6),
            "is_significant_0.05": pvalues < 0.05,
        }
    ).sort_values("f_score", ascending=False)
    logger.info("ANOVA F-scores computed for %d features.", len(cont_cols))
    return result
