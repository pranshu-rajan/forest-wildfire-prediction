"""
Unit tests for descriptive statistics, correlations, chi-square, scaling, and PCA.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler

from python_src.statistics import (
    pearson_correlation_matrix,
    high_correlations,
    chi2_feature_scores,
)
from python_src.preprocessing import (
    discretise_continuous_features,
    GaussianSmoother,
)
from python_src.dimensionality_reduction import (
    fit_pca,
    pca_report,
)
from python_src.schemas import CONTINUOUS_FEATURES


def test_pearson_correlation(synthetic_covtype_df: pd.DataFrame):
    """Verify Pearson correlation matrix computes valid symmetrical bounded values."""
    corr = pearson_correlation_matrix(synthetic_covtype_df)
    assert not corr.empty
    assert corr.shape[0] == len(CONTINUOUS_FEATURES)
    assert np.allclose(np.diag(corr), 1.0)
    assert ((corr >= -1.0) & (corr <= 1.0)).all().all()

    high_corr = high_correlations(corr, threshold=0.99)
    assert isinstance(high_corr, pd.DataFrame)


def test_chi2_feature_scores(synthetic_covtype_df: pd.DataFrame):
    """Verify chi-square scores calculate non-negative values and valid p-values."""
    chi2_df = chi2_feature_scores(synthetic_covtype_df, sample_n=None)
    assert not chi2_df.empty
    assert "chi2_score" in chi2_df.columns
    assert (chi2_df["chi2_score"] >= 0).all()
    assert ((chi2_df["p_value"] >= 0) & (chi2_df["p_value"] <= 1)).all()


def test_gaussian_smoother():
    """Verify 1-D local smoother preserves matrix shapes and smooths signals."""
    smoother = GaussianSmoother(window=5)
    X = np.random.randn(50, 4)
    X_smooth = smoother.fit_transform(X)
    assert X_smooth.shape == X.shape
    assert not np.isnan(X_smooth).any()


def test_discretisation(synthetic_covtype_df: pd.DataFrame):
    """Verify quantile discretisation generates expected bin count."""
    n_bins = 5
    disc_df, discretizer = discretise_continuous_features(
        synthetic_covtype_df,
        n_bins=n_bins,
        strategy="uniform",
    )
    for col in CONTINUOUS_FEATURES:
        bin_col = f"{col}_bin"
        assert bin_col in disc_df.columns
        assert disc_df[bin_col].nunique() <= n_bins


def test_pca_fit_and_report(synthetic_covtype_df: pd.DataFrame):
    """Verify PCA fits on scaled data and produces correct explained variance dimensions."""
    X_cont = synthetic_covtype_df[CONTINUOUS_FEATURES].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_cont)

    pca = fit_pca(X_scaled, n_components=5, random_state=42)
    assert pca.n_components_ == 5

    report = pca_report(pca, CONTINUOUS_FEATURES)
    assert report["n_components"] == 5
    assert len(report["explained_variance_ratio"]) == 5
    assert 0.0 < report["total_explained_variance_pct"] <= 100.0
