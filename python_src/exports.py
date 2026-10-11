"""
Exports module: generate KNIME-ready and Tableau-ready output files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from python_src.logging_config import get_logger
from python_src.schemas import (
    ALL_FEATURES,
    CONTINUOUS_FEATURES,
    COVER_TYPE_NAMES,
    TARGET_COLUMN,
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# KNIME exports
# ---------------------------------------------------------------------------

def export_covertype_curated(
    df: pd.DataFrame,
    out_dir: Path,
    sample_n: int | None = 50_000,
) -> Path:
    """Export a curated (feature-only) Covertype CSV for KNIME consumption."""
    out_dir.mkdir(parents=True, exist_ok=True)
    export_cols = ALL_FEATURES + [TARGET_COLUMN]
    export_df = df[[c for c in export_cols if c in df.columns]]
    if sample_n and len(export_df) > sample_n:
        export_df = export_df.sample(n=sample_n, random_state=42)
        logger.info("KNIME export: sampled %d rows for file size.", sample_n)
    path = out_dir / "covertype_curated.csv"
    export_df.to_csv(path, index=False)
    logger.info("Exported curated CSV to %s (%d rows).", path, len(export_df))
    return path


def export_class_distribution(df: pd.DataFrame, out_dir: Path) -> Path:
    """Export class distribution CSV."""
    dist = df[TARGET_COLUMN].value_counts().sort_index().reset_index()
    dist.columns = ["Cover_Type", "count"]
    dist["pct"] = (dist["count"] / dist["count"].sum() * 100).round(2)
    dist["cover_name"] = dist["Cover_Type"].map(COVER_TYPE_NAMES)
    path = out_dir / "class_distribution.csv"
    dist.to_csv(path, index=False)
    logger.info("Exported class distribution to %s.", path)
    return path


def export_data_quality_report(quality_df: pd.DataFrame, out_dir: Path) -> Path:
    """Export data quality report CSV."""
    path = out_dir / "data_quality_report.csv"
    quality_df.to_csv(path, index=False)
    logger.info("Exported data quality report to %s.", path)
    return path


def export_descriptive_statistics(stats_df: pd.DataFrame, out_dir: Path) -> Path:
    """Export descriptive statistics CSV."""
    path = out_dir / "descriptive_statistics.csv"
    stats_df.to_csv(path, index=False)
    logger.info("Exported descriptive statistics to %s.", path)
    return path


def export_feature_selection_results(
    combined_ranking: pd.DataFrame,
    out_dir: Path,
) -> Path:
    """Export feature selection rankings CSV."""
    path = out_dir / "feature_selection_results.csv"
    combined_ranking.to_csv(path, index=False)
    logger.info("Exported feature selection results to %s.", path)
    return path


def export_pca_scores(pca_scores_df: pd.DataFrame, out_dir: Path, max_rows: int = 50_000) -> Path:
    """Export PCA scores CSV (sampled if large)."""
    if len(pca_scores_df) > max_rows:
        pca_scores_df = pca_scores_df.sample(n=max_rows, random_state=42)
    path = out_dir / "pca_scores.csv"
    pca_scores_df.to_csv(path, index=False)
    logger.info("Exported PCA scores to %s.", path)
    return path


def export_classification_metrics(metrics_df: pd.DataFrame, out_dir: Path) -> Path:
    """Export model metrics summary CSV."""
    path = out_dir / "classification_metrics.csv"
    metrics_df.to_csv(path, index=False)
    logger.info("Exported classification metrics to %s.", path)
    return path


def export_prediction_results(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    out_dir: Path,
    model_name: str = "best_model",
    max_rows: int = 10_000,
) -> Path:
    """Export true vs predicted labels for test set."""
    df = pd.DataFrame({
        "true_cover_type": y_true,
        "predicted_cover_type": y_pred,
        "true_name": [COVER_TYPE_NAMES.get(int(v), str(v)) for v in y_true],
        "predicted_name": [COVER_TYPE_NAMES.get(int(v), str(v)) for v in y_pred],
        "correct": (y_true == y_pred).astype(int),
    })
    if len(df) > max_rows:
        df = df.sample(n=max_rows, random_state=42)
    path = out_dir / "prediction_results.csv"
    df.to_csv(path, index=False)
    logger.info("Exported prediction results to %s.", path)
    return path


def export_clustering_results(clustering_results_path: Path, out_dir: Path) -> Path:
    """Copy clustering results CSV to export dir."""
    import shutil
    dst = out_dir / "clustering_results.csv"
    if clustering_results_path.exists():
        shutil.copy2(clustering_results_path, dst)
        logger.info("Exported clustering results to %s.", dst)
    else:
        logger.warning("Clustering results file not found at %s.", clustering_results_path)
    return dst


def export_data_dictionary(out_dir: Path) -> Path:
    """Generate a data dictionary CSV for KNIME and Tableau."""
    from python_src.schemas import (
        BINARY_FEATURES, CONTINUOUS_FEATURES, COVER_TYPE_NAMES,
        CONTINUOUS_VALID_RANGES, WILDERNESS_AREA_NAMES, SOIL_FEATURES,
    )

    rows = []

    for col in CONTINUOUS_FEATURES:
        lo, hi = CONTINUOUS_VALID_RANGES.get(col, (None, None))
        rows.append({
            "column": col,
            "type": "Continuous",
            "description": f"Terrain/distance/hillshade measurement. Range: [{lo}, {hi}].",
            "valid_range": f"[{lo}, {hi}]",
            "encoding": "raw integer",
        })

    for col in [f"Wilderness_Area{i}" for i in range(1, 5)]:
        area_name = WILDERNESS_AREA_NAMES.get(col, col)
        rows.append({
            "column": col,
            "type": "Binary",
            "description": f"1 if observation is in {area_name} Wilderness Area, else 0.",
            "valid_range": "{0, 1}",
            "encoding": "one-hot",
        })

    for col in SOIL_FEATURES:
        rows.append({
            "column": col,
            "type": "Binary",
            "description": f"1 if the soil type matches {col}, else 0.",
            "valid_range": "{0, 1}",
            "encoding": "one-hot",
        })

    rows.append({
        "column": TARGET_COLUMN,
        "type": "Categorical (Target)",
        "description": "Forest cover type class. " + ", ".join(f"{k}={v}" for k, v in COVER_TYPE_NAMES.items()),
        "valid_range": "{1, 2, 3, 4, 5, 6, 7}",
        "encoding": "integer label",
    })

    df = pd.DataFrame(rows)
    path = out_dir / "data_dictionary.csv"
    df.to_csv(path, index=False)
    logger.info("Data dictionary exported to %s (%d entries).", path, len(df))
    return path


# ---------------------------------------------------------------------------
# Tableau exports
# ---------------------------------------------------------------------------

def export_terrain_summary_by_cover(df: pd.DataFrame, out_dir: Path) -> Path:
    """Terrain feature means by Cover Type for Tableau Dashboard 2."""
    cont_cols = [c for c in CONTINUOUS_FEATURES if c in df.columns]
    grouped = df.groupby(TARGET_COLUMN)[cont_cols].agg(["mean", "median", "std"]).round(2)
    grouped.columns = ["_".join(c) for c in grouped.columns]
    grouped["cover_name"] = [COVER_TYPE_NAMES.get(i, str(i)) for i in grouped.index]
    grouped = grouped.reset_index()
    path = out_dir / "terrain_summary_by_cover_type.csv"
    grouped.to_csv(path, index=False)
    logger.info("Exported terrain summary to %s.", path)
    return path


def export_wilderness_cover_summary(df: pd.DataFrame, out_dir: Path) -> Path:
    """Wilderness area × Cover Type counts for Tableau."""
    from python_src.schemas import WILDERNESS_FEATURES, WILDERNESS_AREA_NAMES
    wa_cols = [c for c in WILDERNESS_FEATURES if c in df.columns]
    df2 = df.copy()
    df2["wilderness_area"] = df2[wa_cols].idxmax(axis=1).map(WILDERNESS_AREA_NAMES)
    ct = pd.crosstab(df2["wilderness_area"], df2[TARGET_COLUMN])
    ct.columns = [COVER_TYPE_NAMES.get(c, str(c)) for c in ct.columns]
    ct = ct.reset_index()
    path = out_dir / "wilderness_cover_summary.csv"
    ct.to_csv(path, index=False)
    return path


def export_wildfire_screening_aggregates(df: pd.DataFrame, out_dir: Path) -> Path:
    """Export terrain and distance based wildfire risk screening aggregates.

    IMPORTANT: This is an exploratory terrain screening score, NOT a calibrated
    probability of future fire ignition. It combines:
    - Distance_To_Fire_Points (proximity factor)
    - Slope (steeper slopes accelerate uphill fire spread)
    - Hillshade_Noon / Aspect (solar radiation and fuel drying)
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    df_calc = df.copy()
    
    # Compute normalized proxy index [0, 100]
    # Invert distance so closer = higher risk
    if "Horizontal_Distance_To_Fire_Points" in df_calc.columns:
        max_dist = df_calc["Horizontal_Distance_To_Fire_Points"].quantile(0.99)
        dist_factor = 1.0 - (df_calc["Horizontal_Distance_To_Fire_Points"].clip(0, max_dist) / max_dist)
    else:
        dist_factor = 0.5

    slope_factor = df_calc["Slope"].clip(0, 60) / 60.0 if "Slope" in df_calc.columns else 0.5
    sun_factor = df_calc["Hillshade_Noon"].clip(0, 255) / 255.0 if "Hillshade_Noon" in df_calc.columns else 0.5

    # Screening score: 40% proximity + 35% slope + 25% solar exposure
    df_calc["screening_risk_score"] = (0.40 * dist_factor + 0.35 * slope_factor + 0.25 * sun_factor) * 100.0
    df_calc["screening_risk_score"] = df_calc["screening_risk_score"].round(1)

    # Classify into risk tiers
    df_calc["risk_tier"] = pd.cut(
        df_calc["screening_risk_score"],
        bins=[-1, 35, 65, 101],
        labels=["Low Screening Risk", "Moderate Screening Risk", "High Screening Risk"],
    )

    # Aggregate by Cover Type and Wilderness Area
    from python_src.schemas import WILDERNESS_FEATURES, WILDERNESS_AREA_NAMES
    wa_cols = [c for c in WILDERNESS_FEATURES if c in df_calc.columns]
    if wa_cols:
        df_calc["wilderness_area"] = df_calc[wa_cols].idxmax(axis=1).map(WILDERNESS_AREA_NAMES)
    else:
        df_calc["wilderness_area"] = "Unknown"

    agg = df_calc.groupby([TARGET_COLUMN, "wilderness_area", "risk_tier"], observed=False).agg(
        observation_count=("Elevation", "count"),
        mean_elevation=("Elevation", "mean"),
        mean_slope=("Slope", "mean"),
        mean_dist_to_fire_points=("Horizontal_Distance_To_Fire_Points", "mean"),
        mean_screening_risk_score=("screening_risk_score", "mean"),
    ).reset_index()

    agg["cover_name"] = agg[TARGET_COLUMN].map(COVER_TYPE_NAMES)
    path = out_dir / "wildfire_screening_aggregates.csv"
    agg.to_csv(path, index=False)
    logger.info("Exported wildfire screening aggregates to %s.", path)
    return path

