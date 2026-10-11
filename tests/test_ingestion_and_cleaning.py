"""
Unit tests for data ingestion, auditing, and synthetic cleaning experiment.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from python_src.cleaning import generate_quality_report, clean_covtype
from python_src.synthetic_data import (
    inject_missing_values,
    apply_median_imputation,
    build_quality_snapshot,
    validate_cleaning_result,
    generate_markdown_report,
)
from python_src.schemas import (
    ALL_FEATURES,
    CONTINUOUS_FEATURES,
    TARGET_COLUMN,
)


def test_schema_conformance(synthetic_covtype_df: pd.DataFrame):
    """Verify synthetic fixture has all required features and correct target column."""
    for col in ALL_FEATURES:
        assert col in synthetic_covtype_df.columns, f"Missing column: {col}"
    assert TARGET_COLUMN in synthetic_covtype_df.columns
    assert len(synthetic_covtype_df) == 200


def test_compute_quality_summary(synthetic_covtype_df: pd.DataFrame):
    """Verify data quality summary reports zero missing values and correct data types."""
    summary_df = generate_quality_report(synthetic_covtype_df)
    assert not summary_df.empty
    assert "n_missing" in summary_df.columns
    assert summary_df["n_missing"].sum() == 0


def test_synthetic_missing_value_injection(synthetic_covtype_df: pd.DataFrame):
    """Verify injection injects exactly the specified number of missing cells into continuous features only."""
    n_inject = 50
    corrupted_df, record = inject_missing_values(
        synthetic_covtype_df,
        n_inject=n_inject,
        seed=123,
    )

    # Check total missing cells
    total_missing = corrupted_df.isna().sum().sum()
    assert total_missing == n_inject
    assert record.n_injected == n_inject

    # Verify no missing values in target or binary columns
    assert corrupted_df[TARGET_COLUMN].isna().sum() == 0
    non_cont = [c for c in synthetic_covtype_df.columns if c not in CONTINUOUS_FEATURES]
    assert corrupted_df[non_cont].isna().sum().sum() == 0

    # Verify median imputation restores complete dataset
    imputed_df, audit = apply_median_imputation(corrupted_df)
    assert imputed_df.isna().sum().sum() == 0
    assert audit.to_dict()["total_imputed"] == n_inject


def test_full_synthetic_experiment_workflow(synthetic_covtype_df: pd.DataFrame):
    """Verify end-to-end synthetic experiment generation and audit artifacts."""
    corrupted_df, record = inject_missing_values(
        synthetic_covtype_df,
        n_inject=40,
        seed=42,
    )
    before_snap = build_quality_snapshot(corrupted_df)
    assert before_snap["n_missing"].sum() == 40

    imputed_df, audit = apply_median_imputation(corrupted_df)
    after_snap = build_quality_snapshot(imputed_df)
    assert after_snap["n_missing"].sum() == 0

    checks = validate_cleaning_result(
        baseline=synthetic_covtype_df,
        corrupted=corrupted_df,
        cleaned=imputed_df,
        injection_record=record,
    )
    assert checks["all_checks_passed"] is True

    md = generate_markdown_report(checks, record, audit, len(synthetic_covtype_df))
    assert "# Synthetic Missing-Value Cleaning Experiment Report" in md

