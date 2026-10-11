"""
Script 11: Export integration datasets for KNIME and Tableau.

Generates all required flat-file exports, schema definitions, and summary tables
consumed by:
- KNIME workflows (exports/knime/)
- Tableau dashboards (exports/tableau/)

Outputs
-------
exports/knime/
  - covertype_curated.csv
  - class_distribution.csv
  - data_quality_report.csv
  - descriptive_statistics.csv
  - feature_selection_results.csv
  - pca_scores.csv
  - classification_metrics.csv
  - prediction_results.csv
  - clustering_results.csv
  - forest_fires_regression_results.csv
  - data_dictionary.csv

exports/tableau/
  - data_dictionary.csv
  - terrain_summary_by_cover_type.csv
  - wilderness_cover_summary.csv
  - wildfire_screening_aggregates.csv
  - cover_distribution.csv
  - classification_metrics.csv
  - covtype_tableau_sample.csv
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from python_src.config import settings
from python_src.ingestion import load_raw_covtype
from python_src.logging_config import get_logger, setup_logging
from python_src.exports import (
    export_covertype_curated,
    export_class_distribution,
    export_data_quality_report,
    export_descriptive_statistics,
    export_feature_selection_results,
    export_pca_scores,
    export_classification_metrics,
    export_data_dictionary,
    export_terrain_summary_by_cover,
    export_wilderness_cover_summary,
    export_wildfire_screening_aggregates,
)

setup_logging()
logger = get_logger(__name__)


def main() -> int:
    settings.ensure_dirs()
    logger.info("=== Preparing KNIME & Tableau Integration Exports ===")

    df = load_raw_covtype(settings.raw_covtype)

    # 1. KNIME Exports
    logger.info("Exporting KNIME assets...")
    export_covertype_curated(df, settings.knime_exports_dir, sample_n=50_000)
    export_class_distribution(df, settings.knime_exports_dir)
    export_data_dictionary(settings.knime_exports_dir)

    # Copy generated reports/statistics to KNIME exports if available
    stats_mappings = {
        settings.statistics_dir / "descriptive_statistics.csv": settings.knime_exports_dir / "descriptive_statistics.csv",
        settings.statistics_dir / "data_quality_report.csv": settings.knime_exports_dir / "data_quality_report.csv",
        settings.statistics_dir / "feature_ranking_combined.csv": settings.knime_exports_dir / "feature_selection_results.csv",
        settings.statistics_dir / "pca_scores.csv": settings.knime_exports_dir / "pca_scores.csv",
        settings.statistics_dir / "classification_metrics_summary.csv": settings.knime_exports_dir / "classification_metrics.csv",
        settings.statistics_dir / "clustering_results.csv": settings.knime_exports_dir / "clustering_results.csv",
        settings.statistics_dir / "forest_fires_regression_results.csv": settings.knime_exports_dir / "forest_fires_regression_results.csv",
    }
    for src, dst in stats_mappings.items():
        if src.exists():
            shutil.copy2(src, dst)
            logger.info("Copied %s -> %s", src.name, dst)

    # 2. Tableau Exports
    logger.info("Exporting Tableau assets...")
    settings.tableau_exports_dir.mkdir(parents=True, exist_ok=True)
    export_data_dictionary(settings.tableau_exports_dir)
    export_terrain_summary_by_cover(df, settings.tableau_exports_dir)
    export_wilderness_cover_summary(df, settings.tableau_exports_dir)
    export_wildfire_screening_aggregates(df, settings.tableau_exports_dir)

    # Class distribution for Dashboard 1
    export_class_distribution(df, settings.tableau_exports_dir)

    # Classification metrics for Dashboard 3
    clf_src = settings.statistics_dir / "classification_metrics_summary.csv"
    if clf_src.exists():
        shutil.copy2(clf_src, settings.tableau_exports_dir / "classification_metrics.csv")

    # Cluster profiles for Dashboard 3
    cl_src = settings.statistics_dir / "cluster_profiles.csv"
    if cl_src.exists():
        shutil.copy2(cl_src, settings.tableau_exports_dir / "cluster_profiles.csv")

    # Stratified multi-dimensional sample (20,000 rows) for rich Tableau workbook exploration
    sample_path = settings.tableau_exports_dir / "covtype_tableau_sample.csv"
    sample_df = df.sample(n=min(20_000, len(df)), random_state=settings.random_seed)
    sample_df.to_csv(sample_path, index=False)
    logger.info("Exported Tableau sample (%d rows) to %s", len(sample_df), sample_path)

    logger.info("✓ Integration export complete. Assets ready in exports/knime/ and exports/tableau/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
