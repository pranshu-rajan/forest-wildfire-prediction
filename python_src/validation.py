"""
Data validation module: schema, type, range, and integrity checks.

Validation is non-destructive — every check is recorded in the audit log
but no rows or columns are silently dropped.

Raises ``DataValidationError`` when a *fatal* constraint is violated.
Emits warnings for *advisory* issues (outliers, sparse columns, etc.).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from python_src.logging_config import get_logger
from python_src.schemas import (
    ALL_FEATURES,
    BINARY_FEATURES,
    CONTINUOUS_FEATURES,
    CONTINUOUS_VALID_RANGES,
    RECORD_ID_COLUMN,
    SOIL_FEATURES,
    TARGET_CLASSES,
    TARGET_COLUMN,
    WILDERNESS_FEATURES,
)

logger = get_logger(__name__)


class DataValidationError(Exception):
    """Raised when a fatal data-quality constraint is violated."""


@dataclass
class ValidationReport:
    """Accumulated results from all validation checks."""

    checks: list[dict[str, Any]] = field(default_factory=list)
    fatal_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    def add(self, name: str, passed: bool, severity: str, detail: str) -> None:
        entry = {
            "check": name,
            "passed": passed,
            "severity": severity,
            "detail": detail,
        }
        self.checks.append(entry)
        if not passed:
            if severity == "FATAL":
                self.fatal_count += 1
                logger.error("FATAL  %s: %s", name, detail)
            elif severity == "WARNING":
                self.warning_count += 1
                logger.warning("WARN   %s: %s", name, detail)
        else:
            self.info_count += 1
            logger.info("PASS   %s: %s", name, detail)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": {
                "total_checks": len(self.checks),
                "passed": sum(1 for c in self.checks if c["passed"]),
                "fatal_failures": self.fatal_count,
                "warnings": self.warning_count,
            },
            "checks": self.checks,
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        logger.info("Validation report saved to %s", path)

    def raise_if_fatal(self) -> None:
        if self.fatal_count:
            raise DataValidationError(
                f"{self.fatal_count} fatal validation check(s) failed. "
                "Review the validation report for details."
            )


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_file_exists(path: Path, report: ValidationReport) -> bool:
    ok = path.exists() and path.is_file()
    report.add(
        "file_exists",
        ok,
        "FATAL",
        f"'{path}' {'exists' if ok else 'NOT FOUND'}",
    )
    return ok


def check_column_names(df: pd.DataFrame, report: ValidationReport) -> None:
    expected = set(ALL_FEATURES + [TARGET_COLUMN])
    # record_id is optional (added by ingestion module)
    actual = set(df.columns) - {RECORD_ID_COLUMN}
    missing_cols = expected - actual
    extra_cols = actual - expected

    report.add(
        "expected_columns_present",
        len(missing_cols) == 0,
        "FATAL",
        f"Missing columns: {sorted(missing_cols)}" if missing_cols else "All 55 expected columns present.",
    )
    report.add(
        "no_extra_columns",
        len(extra_cols) == 0,
        "WARNING",
        f"Unexpected extra columns: {sorted(extra_cols)}" if extra_cols else "No unexpected columns.",
    )


def check_row_column_counts(df: pd.DataFrame, report: ValidationReport) -> None:
    n_rows, n_cols = df.shape
    expected_feature_cols = len(ALL_FEATURES)
    # +1 for target, maybe +1 for record_id
    report.add(
        "row_count",
        n_rows > 0,
        "FATAL",
        f"{n_rows:,} rows found.",
    )
    actual_feature_cols = len([c for c in df.columns if c not in (TARGET_COLUMN, RECORD_ID_COLUMN)])
    report.add(
        "feature_column_count",
        actual_feature_cols == expected_feature_cols,
        "FATAL",
        f"Expected {expected_feature_cols} feature columns, found {actual_feature_cols}.",
    )
    logger.info("Dataset shape: %d rows × %d columns", n_rows, n_cols)


def check_dtypes(df: pd.DataFrame, report: ValidationReport) -> None:
    non_numeric = [
        col for col in df.columns
        if col != RECORD_ID_COLUMN and not pd.api.types.is_numeric_dtype(df[col])
    ]
    report.add(
        "all_columns_numeric",
        len(non_numeric) == 0,
        "FATAL",
        f"Non-numeric columns: {non_numeric}" if non_numeric else "All columns are numeric.",
    )


def check_missing_values(df: pd.DataFrame, report: ValidationReport) -> pd.Series:
    missing = df.isnull().sum()
    total_missing = int(missing.sum())
    report.add(
        "no_missing_values",
        total_missing == 0,
        "WARNING",
        f"Total missing cells: {total_missing}",
    )
    return missing


def check_duplicates(df: pd.DataFrame, report: ValidationReport) -> int:
    cols = [c for c in df.columns if c != RECORD_ID_COLUMN]
    n_dup = int(df.duplicated(subset=cols).sum())
    report.add(
        "no_exact_duplicates",
        n_dup == 0,
        "WARNING",
        f"Exact duplicate rows (excluding record_id): {n_dup}",
    )
    return n_dup


def check_target_labels(df: pd.DataFrame, report: ValidationReport) -> None:
    if TARGET_COLUMN not in df.columns:
        return
    actual = set(df[TARGET_COLUMN].unique().tolist())
    expected = set(TARGET_CLASSES)
    unexpected = actual - expected
    missing_classes = expected - actual
    report.add(
        "target_labels_valid",
        len(unexpected) == 0,
        "FATAL",
        f"Unexpected target values: {unexpected}" if unexpected else "All target labels in {1..7}.",
    )
    if missing_classes:
        report.add(
            "all_classes_represented",
            False,
            "WARNING",
            f"Classes not present in data: {sorted(missing_classes)}",
        )


def check_continuous_ranges(df: pd.DataFrame, report: ValidationReport) -> dict[str, dict]:
    results: dict[str, dict] = {}
    for col, (lo, hi) in CONTINUOUS_VALID_RANGES.items():
        if col not in df.columns:
            continue
        n_below = int((df[col] < lo).sum())
        n_above = int((df[col] > hi).sum())
        ok = (n_below == 0) and (n_above == 0)
        results[col] = {"below_range": n_below, "above_range": n_above, "min": float(df[col].min()), "max": float(df[col].max())}
        report.add(
            f"range_{col}",
            ok,
            "WARNING",
            f"{col}: [{df[col].min():.0f}, {df[col].max():.0f}], "
            f"{n_below} below {lo}, {n_above} above {hi}.",
        )
    return results


def check_binary_indicators(df: pd.DataFrame, report: ValidationReport) -> None:
    bad_cols = []
    for col in BINARY_FEATURES:
        if col not in df.columns:
            continue
        unique_vals = set(df[col].unique().tolist())
        if not unique_vals.issubset({0, 1}):
            bad_cols.append(col)
    report.add(
        "binary_features_valid",
        len(bad_cols) == 0,
        "FATAL",
        f"Non-binary values in: {bad_cols}" if bad_cols else "All binary indicators contain only 0/1.",
    )


def check_onehot_integrity(df: pd.DataFrame, report: ValidationReport) -> None:
    # Wilderness: exactly one active per row
    wa_cols = [c for c in WILDERNESS_FEATURES if c in df.columns]
    if wa_cols:
        wa_sum = df[wa_cols].sum(axis=1)
        bad_wa = int((wa_sum != 1).sum())
        report.add(
            "wilderness_onehot_integrity",
            bad_wa == 0,
            "WARNING",
            f"Rows where wilderness area sum ≠ 1: {bad_wa}",
        )

    # Soil: at least one active per row (some rows may have multiple)
    soil_cols = [c for c in SOIL_FEATURES if c in df.columns]
    if soil_cols:
        soil_sum = df[soil_cols].sum(axis=1)
        bad_soil_zero = int((soil_sum == 0).sum())
        report.add(
            "soil_type_nonzero_per_row",
            bad_soil_zero == 0,
            "WARNING",
            f"Rows with no active soil type: {bad_soil_zero}",
        )


def check_sparse_columns(df: pd.DataFrame, report: ValidationReport, threshold: float = 0.01) -> dict[str, float]:
    sparse: dict[str, float] = {}
    for col in SOIL_FEATURES:
        if col not in df.columns:
            continue
        freq = float(df[col].mean())
        if freq < threshold:
            sparse[col] = freq
    report.add(
        "sparse_soil_columns",
        len(sparse) == 0,
        "WARNING",
        f"{len(sparse)} soil columns with <{threshold*100:.0f}% activation: {list(sparse.keys())}",
    )
    return sparse


def check_class_imbalance(df: pd.DataFrame, report: ValidationReport) -> pd.Series:
    dist = df[TARGET_COLUMN].value_counts().sort_index()
    majority = int(dist.max())
    minority = int(dist.min())
    ratio = majority / minority if minority > 0 else float("inf")
    report.add(
        "class_imbalance",
        ratio < 10,
        "WARNING",
        f"Imbalance ratio (majority/minority): {ratio:.1f}x. Dist: {dist.to_dict()}",
    )
    return dist


# ---------------------------------------------------------------------------
# Full validation pipeline
# ---------------------------------------------------------------------------

def validate_covtype(df: pd.DataFrame, source_path: Path) -> ValidationReport:
    """Run all validation checks on a loaded Covertype DataFrame.

    Does NOT raise on advisory warnings; only raises on FATAL issues
    when ``report.raise_if_fatal()`` is explicitly called.
    """
    report = ValidationReport()
    check_file_exists(source_path, report)
    check_column_names(df, report)
    check_row_column_counts(df, report)
    check_dtypes(df, report)
    check_missing_values(df, report)
    check_duplicates(df, report)
    check_target_labels(df, report)
    check_continuous_ranges(df, report)
    check_binary_indicators(df, report)
    check_onehot_integrity(df, report)
    check_sparse_columns(df, report)
    check_class_imbalance(df, report)
    return report
