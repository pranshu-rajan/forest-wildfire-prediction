"""
Feature selection module: ranking, filtering, and redundancy removal.

Covers Practical 6b and Unit IV requirements:
- ANOVA F-score ranking
- Chi-square ranking
- Mutual information
- Variance threshold
- Correlation-based redundancy elimination
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_selection import (
    SelectKBest,
    VarianceThreshold,
    chi2,
    f_classif,
    mutual_info_classif,
)
from sklearn.preprocessing import MinMaxScaler

from python_src.logging_config import get_logger
from python_src.schemas import (
    ALL_FEATURES,
    BINARY_FEATURES,
    CONTINUOUS_FEATURES,
    TARGET_COLUMN,
)

logger = get_logger(__name__)


def variance_threshold_filter(
    X: np.ndarray,
    feature_names: list[str],
    threshold: float = 0.01,
) -> tuple[np.ndarray, list[str], list[str]]:
    """Remove features with variance below threshold (typically zero-variance binary cols).

    Returns (X_filtered, kept_names, removed_names).
    """
    vt = VarianceThreshold(threshold=threshold)
    X_filtered = vt.fit_transform(X)
    mask = vt.get_support()
    kept = [f for f, m in zip(feature_names, mask) if m]
    removed = [f for f, m in zip(feature_names, mask) if not m]
    logger.info("VarianceThreshold: kept %d / %d features (removed %d).", len(kept), len(feature_names), len(removed))
    return X_filtered, kept, removed


def anova_feature_ranking(
    X_train: np.ndarray,
    y_train: np.ndarray,
    feature_names: list[str],
) -> pd.DataFrame:
    """Rank features by ANOVA F-score against the target."""
    scores, pvalues = f_classif(X_train, y_train)
    df = pd.DataFrame(
        {
            "feature": feature_names,
            "f_score": np.round(scores, 4),
            "p_value": np.round(pvalues, 6),
            "rank": np.argsort(np.argsort(-scores)) + 1,
        }
    ).sort_values("f_score", ascending=False)
    logger.info("ANOVA ranking: top feature '%s' (F=%.1f).", df.iloc[0]["feature"], df.iloc[0]["f_score"])
    return df


def chi2_feature_ranking(
    X_train: np.ndarray,
    y_train: np.ndarray,
    feature_names: list[str],
) -> pd.DataFrame:
    """Rank features by Chi-square score (requires non-negative X)."""
    # Scale to [0,1] to satisfy chi2 non-negativity requirement
    X_nn = MinMaxScaler().fit_transform(X_train)
    scores, pvalues = chi2(X_nn, y_train)
    df = pd.DataFrame(
        {
            "feature": feature_names,
            "chi2_score": np.round(scores, 4),
            "p_value": np.round(pvalues, 6),
            "rank": np.argsort(np.argsort(-scores)) + 1,
        }
    ).sort_values("chi2_score", ascending=False)
    logger.info("Chi-square ranking: top feature '%s' (χ²=%.1f).", df.iloc[0]["feature"], df.iloc[0]["chi2_score"])
    return df


def mutual_info_feature_ranking(
    X_train: np.ndarray,
    y_train: np.ndarray,
    feature_names: list[str],
    seed: int = 42,
) -> pd.DataFrame:
    """Rank features by mutual information with the target."""
    mi_scores = mutual_info_classif(X_train, y_train, random_state=seed)
    df = pd.DataFrame(
        {
            "feature": feature_names,
            "mutual_info": np.round(mi_scores, 6),
            "rank": np.argsort(np.argsort(-mi_scores)) + 1,
        }
    ).sort_values("mutual_info", ascending=False)
    logger.info("Mutual info ranking: top feature '%s' (MI=%.4f).", df.iloc[0]["feature"], df.iloc[0]["mutual_info"])
    return df


def combined_feature_ranking(
    X_train: np.ndarray,
    y_train: np.ndarray,
    feature_names: list[str],
    seed: int = 42,
) -> pd.DataFrame:
    """Combine ANOVA, Chi2, and MI rankings into a single table."""
    anova = anova_feature_ranking(X_train, y_train, feature_names).set_index("feature")
    chi = chi2_feature_ranking(X_train, y_train, feature_names).set_index("feature")
    mi = mutual_info_feature_ranking(X_train, y_train, feature_names, seed=seed).set_index("feature")

    combined = pd.DataFrame(index=feature_names)
    combined["f_score"] = anova["f_score"]
    combined["f_rank"] = anova["rank"]
    combined["chi2_score"] = chi["chi2_score"]
    combined["chi2_rank"] = chi["rank"]
    combined["mutual_info"] = mi["mutual_info"]
    combined["mi_rank"] = mi["rank"]
    combined["mean_rank"] = combined[["f_rank", "chi2_rank", "mi_rank"]].mean(axis=1)
    combined = combined.sort_values("mean_rank").reset_index().rename(columns={"index": "feature"})
    return combined


def select_top_k_features(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    feature_names: list[str],
    k: int = 20,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Select top-k features by ANOVA F-score. Fit on train only."""
    selector = SelectKBest(f_classif, k=k)
    X_train_sel = selector.fit_transform(X_train, y_train)
    X_test_sel = selector.transform(X_test)
    mask = selector.get_support()
    selected = [f for f, m in zip(feature_names, mask) if m]
    logger.info("SelectKBest (k=%d): selected %s …", k, selected[:5])
    return X_train_sel, X_test_sel, selected


def correlation_based_removal(
    X_train: pd.DataFrame,
    threshold: float = 0.90,
) -> tuple[pd.DataFrame, list[str]]:
    """Greedily drop columns with pairwise Pearson |r| >= threshold.

    Returns (filtered_df, removed_cols).
    """
    corr = X_train.corr(method="pearson").abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    to_drop = [c for c in upper.columns if any(upper[c] > threshold)]
    X_filtered = X_train.drop(columns=to_drop)
    logger.info("Correlation removal (threshold=%.2f): removed %d features: %s", threshold, len(to_drop), to_drop)
    return X_filtered, to_drop
