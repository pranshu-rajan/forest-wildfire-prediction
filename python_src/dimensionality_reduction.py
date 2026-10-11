"""
Dimensionality reduction module: PCA and related analysis.

Covers Practical 6b and Unit IV requirements:
- PCA with explained variance reporting
- Component loading analysis
- Curse of dimensionality discussion
- Comparison of original vs reduced feature spaces
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from python_src.logging_config import get_logger
from python_src.schemas import CONTINUOUS_FEATURES, TARGET_COLUMN

logger = get_logger(__name__)


def fit_pca(
    X_train: np.ndarray,
    n_components: int | float | None = None,
    random_state: int = 42,
) -> PCA:
    """Fit PCA on training data only.

    Parameters
    ----------
    X_train:
        Scaled training feature matrix (standardised first!).
    n_components:
        Number of components or float (variance fraction to retain).
    random_state:
        Random seed for reproducibility.
    """
    pca = PCA(n_components=n_components, random_state=random_state)
    pca.fit(X_train)
    n_comp_used = pca.n_components_
    total_var = float(np.sum(pca.explained_variance_ratio_) * 100)
    logger.info(
        "PCA fitted: %d components explain %.1f%% of variance.",
        n_comp_used, total_var,
    )
    return pca


def pca_report(
    pca: PCA,
    feature_names: list[str],
) -> dict[str, Any]:
    """Generate a comprehensive PCA report dict."""
    evr = pca.explained_variance_ratio_
    cumulative_evr = np.cumsum(evr)

    # Find components needed to reach 90% and 95% variance
    n_90 = int(np.searchsorted(cumulative_evr, 0.90) + 1)
    n_95 = int(np.searchsorted(cumulative_evr, 0.95) + 1)

    report = {
        "n_components": int(pca.n_components_),
        "n_features_in": int(pca.n_features_in_),
        "n_components_for_90pct_variance": n_90,
        "n_components_for_95pct_variance": n_95,
        "total_explained_variance_pct": round(float(np.sum(evr) * 100), 2),
        "explained_variance_ratio": [round(float(x), 6) for x in evr],
        "cumulative_explained_variance": [round(float(x), 6) for x in cumulative_evr],
    }

    # Top loadings per component (first 3 components)
    components_summary = []
    for i, component in enumerate(pca.components_[:min(5, len(pca.components_))]):
        top_idx = np.argsort(np.abs(component))[-5:][::-1]
        top_features = [
            {"feature": feature_names[j] if j < len(feature_names) else f"f{j}",
             "loading": round(float(component[j]), 4)}
            for j in top_idx
        ]
        components_summary.append(
            {
                "component": i + 1,
                "explained_variance_pct": round(float(evr[i] * 100), 2),
                "top_5_loadings": top_features,
            }
        )
    report["component_summaries"] = components_summary

    return report


def pca_scores_dataframe(
    X: np.ndarray,
    pca: PCA,
    n_components: int = 10,
    index: pd.Index | None = None,
) -> pd.DataFrame:
    """Project X into PCA space and return a DataFrame with PC columns."""
    n_comp = min(n_components, pca.n_components_)
    scores = pca.transform(X)[:, :n_comp]
    cols = [f"PC{i+1}" for i in range(n_comp)]
    df = pd.DataFrame(scores, columns=cols, index=index)
    return df


def loadings_dataframe(pca: PCA, feature_names: list[str]) -> pd.DataFrame:
    """Return PCA loadings as a DataFrame (features × components)."""
    n_comp = pca.n_components_
    cols = [f"PC{i+1}" for i in range(n_comp)]
    df = pd.DataFrame(
        pca.components_.T,
        index=feature_names[: pca.n_features_in_],
        columns=cols,
    )
    return df.round(4)


def fit_pca_pipeline(
    X_train: np.ndarray,
    X_test: np.ndarray,
    feature_names: list[str],
    n_components: int | float = 0.95,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray, PCA, StandardScaler, dict]:
    """Fit scaler + PCA on training data, transform both splits.

    Returns (X_train_pca, X_test_pca, pca_obj, scaler_obj, report_dict)
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    pca = fit_pca(X_train_scaled, n_components=n_components, random_state=random_state)
    X_train_pca = pca.transform(X_train_scaled)
    X_test_pca = pca.transform(X_test_scaled)

    report = pca_report(pca, feature_names)
    logger.info(
        "PCA pipeline: %d original features → %d components.",
        len(feature_names), pca.n_components_,
    )
    return X_train_pca, X_test_pca, pca, scaler, report
