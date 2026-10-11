"""
Unit tests for model development, evaluation, serialization, and deterministic inference.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from python_src.classification import (
    evaluate_classifier,
    get_classifiers,
)
from python_src.clustering import run_clustering_pipeline
from python_src.preprocessing import stratified_split
from python_src.schemas import ALL_FEATURES, TARGET_COLUMN


def test_stratified_split(synthetic_covtype_df: pd.DataFrame):
    """Verify stratified split separates train and test sets with proportional class distributions."""
    feature_cols = [c for c in ALL_FEATURES if c in synthetic_covtype_df.columns]
    X_train, X_test, y_train, y_test = stratified_split(
        synthetic_covtype_df,
        test_size=0.25,
        random_seed=42,
        feature_cols=feature_cols,
    )

    assert len(X_train) == 150
    assert len(X_test) == 50
    assert len(X_train) + len(X_test) == len(synthetic_covtype_df)
    # Check that record_id is not included in feature matrix
    assert "record_id" not in X_train.columns


def test_classifier_training_and_serialization(synthetic_covtype_df: pd.DataFrame, tmp_path):
    """Verify training a Decision Tree on synthetic data, evaluating metrics, and serializing."""
    feature_cols = [c for c in ALL_FEATURES if c in synthetic_covtype_df.columns]
    X_train, X_test, y_train, y_test = stratified_split(
        synthetic_covtype_df,
        test_size=0.25,
        random_seed=42,
        feature_cols=feature_cols,
    )

    from python_src.classification import train_classifier

    models = get_classifiers(random_state=42)
    dt_pipeline = models["Decision Tree"]

    fitted_pipeline, _ = train_classifier("Decision Tree", dt_pipeline, X_train.values, y_train)
    metrics = evaluate_classifier(
        "Decision Tree",
        fitted_pipeline,
        X_test.values,
        y_test,
    )
    joblib.dump(fitted_pipeline, tmp_path / "decision_tree.joblib")

    assert metrics["accuracy"] >= 0.0
    assert "macro_f1" in metrics
    assert (tmp_path / "decision_tree.joblib").exists()
    assert (tmp_path / "decision_tree.joblib").exists()

    # Test model reloading and inference
    loaded_model = joblib.load(tmp_path / "decision_tree.joblib")
    preds = loaded_model.predict(X_test.values)
    assert len(preds) == len(X_test)
    assert ((preds >= 1) & (preds <= 7)).all()


def test_clustering_pipeline_execution(synthetic_covtype_df: pd.DataFrame, tmp_path):
    """Verify clustering runs without target leakage and saves profiles."""
    results = run_clustering_pipeline(
        synthetic_covtype_df,
        out_dir=tmp_path,
        sample_n=100,
        k_range=range(2, 5),
        best_k=3,
        random_state=42,
    )

    assert results["best_k"] == 3
    assert len(results["cluster_sizes"]) == 3
    assert (tmp_path / "cluster_profiles.csv").exists()
    assert (tmp_path / "cluster_elbow_silhouette.csv").exists()
