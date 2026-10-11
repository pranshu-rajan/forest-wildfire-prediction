"""
Script 04: Generate EDA — plots, profiles, and the EDA report.

Produces all required EDA visualisations and the programmatic EDA report.

Outputs
-------
- reports/figures/*.png  (all EDA plots)
- reports/statistics/dataset_summary.json
- reports/statistics/class_distribution.csv
- reports/statistics/wilderness_cover_crosstab.csv
- reports/statistics/soil_type_frequency.csv
- reports/statistics/classwise_feature_means.csv
- reports/eda_report.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python_src.config import settings
from python_src.ingestion import load_raw_covtype
from python_src.logging_config import get_logger, setup_logging
from python_src.profiling import (
    classwise_continuous_stats,
    dataset_summary,
    descriptive_statistics,
    soil_type_frequency,
    wilderness_cover_crosstab,
    classify_attribute_types,
)
from python_src.statistics import pearson_correlation_matrix
from python_src.visualization import (
    plot_class_distribution,
    plot_continuous_distributions,
    plot_boxplots,
    plot_correlation_heatmap,
    plot_scatter_elevation_vs_distance,
    plot_wilderness_distribution,
    plot_soil_type_frequency,
    plot_treemap_cover_type,
    plot_radial_cover_distribution,
)
from python_src.reporting import generate_eda_report

setup_logging()
logger = get_logger(__name__)


def main() -> int:
    settings.ensure_dirs()
    logger.info("=== Phase 2: EDA and Visualisations ===")

    df = load_raw_covtype(settings.raw_covtype, add_record_id=True)

    # 1. Dataset summary
    summary = dataset_summary(df)
    with open(settings.statistics_dir / "dataset_summary.json", "w") as fh:
        json.dump(summary, fh, indent=2)

    # 2. Attribute types
    attr_types = classify_attribute_types(df)
    attr_types.to_csv(settings.statistics_dir / "attribute_types.csv", index=False)

    # 3. Class distribution
    from python_src.schemas import TARGET_COLUMN, COVER_TYPE_NAMES
    dist = df[TARGET_COLUMN].value_counts().sort_index().reset_index()
    dist.columns = ["Cover_Type", "count"]
    dist["cover_name"] = dist["Cover_Type"].map(COVER_TYPE_NAMES)
    dist.to_csv(settings.statistics_dir / "class_distribution.csv", index=False)

    # 4. Wilderness/soil analysis
    wc = wilderness_cover_crosstab(df)
    wc.to_csv(settings.statistics_dir / "wilderness_cover_crosstab.csv")

    soil_df = soil_type_frequency(df)
    soil_df.to_csv(settings.statistics_dir / "soil_type_frequency.csv", index=False)

    classwise = classwise_continuous_stats(df)
    classwise.to_csv(settings.statistics_dir / "classwise_feature_means.csv")

    # 5. Correlation
    corr = pearson_correlation_matrix(df)
    corr.to_csv(settings.statistics_dir / "pearson_correlation.csv")

    # 6. Descriptive stats (needed for EDA report)
    stats_df = descriptive_statistics(df)
    stats_df.to_csv(settings.statistics_dir / "descriptive_statistics_full.csv", index=False)

    # 7. All visualisations
    logger.info("Generating visualisations …")
    plot_class_distribution(df, settings.figures_dir)
    plot_continuous_distributions(df, settings.figures_dir)
    plot_boxplots(df, settings.figures_dir)
    plot_correlation_heatmap(corr, settings.figures_dir)
    plot_scatter_elevation_vs_distance(df, settings.figures_dir)
    plot_wilderness_distribution(df, settings.figures_dir)
    plot_soil_type_frequency(soil_df, settings.figures_dir)
    plot_treemap_cover_type(df, settings.figures_dir)
    plot_radial_cover_distribution(df, settings.figures_dir)

    # 8. EDA markdown report
    generate_eda_report(summary, stats_df, settings.reports_dir)

    logger.info("✓ EDA complete. Check reports/figures/ and reports/eda_report.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
