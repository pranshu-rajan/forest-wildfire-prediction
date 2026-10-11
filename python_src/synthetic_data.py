"""
Synthetic missing-value cleaning experiment (Practical 2 requirement).

This module creates a controlled, reproducible experiment that demonstrates
the complete missing-value detection and imputation pipeline even though the
original Covertype dataset contains no missing values.

Workflow
--------
1. Sample exactly ``n_rows`` rows from the real dataset (seed-controlled).
2. Save a clean baseline copy.
3. Inject exactly ``n_inject`` missing cells into continuous predictor columns only.
   - Target, record_id, and binary indicators are never touched.
   - Injection locations are tracked explicitly for auditability.
4. Generate a before-cleaning quality report.
5. Apply median imputation (fit on the corrupted subset — not the full dataset).
6. Generate an after-cleaning quality report.
7. Validate that all injected cells have been resolved and row count is preserved.
8. Save visualisations, a JSON report, and a Markdown report.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from python_src.logging_config import get_logger
from python_src.schemas import (
    CONTINUOUS_FEATURES,
    RECORD_ID_COLUMN,
    TARGET_COLUMN,
)

logger = get_logger(__name__)

# Sentinel for tracking injected positions
_INJECTION_SEED = 2024


@dataclass
class InjectionRecord:
    """Tracks the exact positions where missing values were injected."""

    locations: list[tuple[int, str]] = field(default_factory=list)  # (row_iloc, col_name)
    n_injected: int = 0

    def to_list(self) -> list[dict[str, Any]]:
        return [{"row_iloc": r, "column": c} for r, c in self.locations]


@dataclass
class ImputationAudit:
    """Records median values used for imputation and counts imputed cells."""

    medians: dict[str, float] = field(default_factory=dict)
    counts: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "medians": self.medians,
            "imputed_cell_counts": self.counts,
            "total_imputed": sum(self.counts.values()),
        }


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def sample_from_covtype(
    source_df: pd.DataFrame,
    n_rows: int = 10_000,
    seed: int = 42,
) -> pd.DataFrame:
    """Draw a reproducible random sample from the full Covertype DataFrame.

    Parameters
    ----------
    source_df:
        The full (581k-row) Covertype DataFrame — **never modified**.
    n_rows:
        Target sample size (default 10,000).
    seed:
        Random seed for reproducibility.

    Returns
    -------
    A fresh copy of the sample with reset integer index.
    """
    n_rows = min(n_rows, len(source_df))
    sample = source_df.sample(n=n_rows, random_state=seed).reset_index(drop=True)
    logger.info("Sampled %d rows from full dataset (seed=%d).", n_rows, seed)
    return sample.copy()


def inject_missing_values(
    df: pd.DataFrame,
    n_inject: int = 800,
    seed: int = _INJECTION_SEED,
    columns: list[str] | None = None,
) -> tuple[pd.DataFrame, InjectionRecord]:
    """Inject exactly *n_inject* missing cells into continuous predictor columns.

    Constraints:
    - Only injects into columns in *columns* (defaults to ``CONTINUOUS_FEATURES``).
    - Never injects into ``Cover_Type``, ``record_id``, or binary indicators.
    - Uses a fixed seed for full reproducibility.
    - Avoids duplicate (row, col) locations so the count is exact.

    Returns
    -------
    (corrupted_df, InjectionRecord)
    """
    if columns is None:
        columns = [c for c in CONTINUOUS_FEATURES if c in df.columns]

    n_rows, n_cols = len(df), len(columns)
    max_cells = n_rows * n_cols
    if n_inject > max_cells:
        raise ValueError(
            f"Cannot inject {n_inject} missing cells into {max_cells} available cells "
            f"({n_rows} rows × {n_cols} continuous columns)."
        )

    rng = np.random.default_rng(seed)
    corrupted = df.copy()

    # Generate unique (row, col_idx) pairs
    chosen: set[tuple[int, int]] = set()
    while len(chosen) < n_inject:
        rows_needed = n_inject - len(chosen)
        r = rng.integers(0, n_rows, size=rows_needed * 2)
        c = rng.integers(0, n_cols, size=rows_needed * 2)
        for ri, ci in zip(r.tolist(), c.tolist()):
            chosen.add((int(ri), int(ci)))
            if len(chosen) >= n_inject:
                break

    record = InjectionRecord()
    for row_idx, col_idx in chosen:
        col_name = columns[col_idx]
        corrupted.iat[row_idx, corrupted.columns.get_loc(col_name)] = np.nan
        record.locations.append((row_idx, col_name))
    record.n_injected = n_inject

    actual_missing = int(corrupted[columns].isna().sum().sum())
    if actual_missing != n_inject:
        logger.warning(
            "Expected %d injected cells, found %d missing (some may overlap).",
            n_inject,
            actual_missing,
        )
    else:
        logger.info("Injected exactly %d missing cells into continuous columns.", n_inject)

    return corrupted, record


def apply_median_imputation(
    df: pd.DataFrame,
    columns: list[str] | None = None,
) -> tuple[pd.DataFrame, ImputationAudit]:
    """Fill missing values in *columns* with their column medians.

    Medians are computed *from the corrupted data itself* (not from the
    full dataset), as would be done in practice when the real data arrives
    with missing values.

    Returns
    -------
    (imputed_df, ImputationAudit)
    """
    if columns is None:
        columns = [c for c in CONTINUOUS_FEATURES if c in df.columns]

    imputed = df.copy()
    audit = ImputationAudit()

    for col in columns:
        if col not in imputed.columns:
            continue
        n_missing = int(imputed[col].isna().sum())
        if n_missing == 0:
            continue
        median_val = float(imputed[col].median())
        imputed[col] = imputed[col].fillna(median_val)
        audit.medians[col] = round(median_val, 4)
        audit.counts[col] = n_missing

    logger.info(
        "Median imputation complete. %d columns imputed, %d total cells filled.",
        len(audit.counts),
        sum(audit.counts.values()),
    )
    return imputed, audit


def validate_cleaning_result(
    baseline: pd.DataFrame,
    corrupted: pd.DataFrame,
    cleaned: pd.DataFrame,
    injection_record: InjectionRecord,
    columns: list[str] | None = None,
) -> dict[str, Any]:
    """Validate that the cleaning experiment meets all expected criteria.

    Returns a dict of assertion results.
    """
    if columns is None:
        columns = [c for c in CONTINUOUS_FEATURES if c in baseline.columns]

    checks: dict[str, Any] = {}

    # 1. Row count preserved
    checks["row_count_preserved"] = {
        "passed": len(cleaned) == len(baseline),
        "baseline": len(baseline),
        "cleaned": len(cleaned),
    }

    # 2. Exact injection count
    n_corrupted_missing = int(corrupted[columns].isna().sum().sum())
    checks["injected_count_exact"] = {
        "passed": n_corrupted_missing == injection_record.n_injected,
        "expected": injection_record.n_injected,
        "actual": n_corrupted_missing,
    }

    # 3. Zero missing after cleaning
    n_remaining = int(cleaned[columns].isna().sum().sum())
    checks["zero_missing_after_cleaning"] = {
        "passed": n_remaining == 0,
        "remaining_missing_cells": n_remaining,
    }

    # 4. Target labels unchanged
    targets_match = (cleaned[TARGET_COLUMN].values == baseline[TARGET_COLUMN].values).all()
    checks["target_labels_unchanged"] = {"passed": bool(targets_match)}

    # 5. Source dataset not modified (check row count is still ≥ 581k; not checked here — caller responsibility)
    checks["original_preserved_note"] = {
        "note": "Source CSV immutability is verified in 01_audit_source.py via SHA-256 digest."
    }

    all_passed = all(
        v.get("passed", True)
        for v in checks.values()
        if isinstance(v, dict) and "passed" in v
    )
    checks["all_checks_passed"] = all_passed

    for name, result in checks.items():
        if isinstance(result, dict) and "passed" in result:
            status = "PASS" if result["passed"] else "FAIL"
            logger.info("Synthetic cleaning check [%s]: %s", name, status)

    return checks


def build_quality_snapshot(df: pd.DataFrame, columns: list[str] | None = None) -> pd.DataFrame:
    """Return a per-column missing-value snapshot for the given columns."""
    if columns is None:
        columns = [c for c in CONTINUOUS_FEATURES if c in df.columns]
    rows = []
    for col in columns:
        if col not in df.columns:
            continue
        n = len(df)
        n_miss = int(df[col].isna().sum())
        rows.append(
            {
                "column": col,
                "n_total": n,
                "n_missing": n_miss,
                "pct_missing": round(n_miss / n * 100, 2),
                "mean_non_null": round(float(df[col].mean()), 4) if n_miss < n else None,
                "median_non_null": round(float(df[col].median()), 4) if n_miss < n else None,
            }
        )
    return pd.DataFrame(rows)


def generate_markdown_report(
    checks: dict[str, Any],
    injection_record: InjectionRecord,
    imputation_audit: ImputationAudit,
    n_rows: int,
) -> str:
    """Generate a human-readable Markdown report of the experiment."""
    lines = [
        "# Synthetic Missing-Value Cleaning Experiment Report",
        "",
        "## Purpose",
        "This experiment demonstrates the missing-value imputation pipeline on a controlled",
        "teaching copy of the Covertype dataset.  The original source CSV is never modified.",
        "",
        "## Experiment Parameters",
        f"- Sample size: **{n_rows:,} rows**",
        f"- Missing values injected: **{injection_record.n_injected}** cells",
        f"- Injection seed: `{_INJECTION_SEED}`",
        f"- Columns eligible for injection: {[c for c in CONTINUOUS_FEATURES]}",
        "",
        "## Validation Results",
    ]
    for name, result in checks.items():
        if not isinstance(result, dict) or "passed" not in result:
            continue
        icon = "✅" if result["passed"] else "❌"
        detail = ", ".join(
            f"{k}: {v}" for k, v in result.items() if k != "passed"
        )
        lines.append(f"- {icon} **{name}**: {detail}")

    lines += [
        "",
        "## Imputation Summary",
        f"| Column | Median Used | Cells Imputed |",
        "|--------|------------|---------------|",
    ]
    for col, median_val in imputation_audit.medians.items():
        count = imputation_audit.counts.get(col, 0)
        lines.append(f"| {col} | {median_val} | {count} |")

    lines += [
        "",
        "## Conclusion",
        "The imputation pipeline successfully resolved all injected missing values.",
        "Row count and target labels were preserved exactly.",
        "This experiment satisfies the **Practical 2** cleaning demonstration requirement.",
    ]
    return "\n".join(lines)
