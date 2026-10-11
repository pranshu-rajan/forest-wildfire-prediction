"""
Script 10: Train and evaluate Forest Fires regression models (Practical 9).

Note: The Forest Fires dataset (UCI) is completely separate from Covertype.
The target variable is `area` (burned area in hectares).
Because `area` is heavily zero-inflated and right-skewed, log1p transformation is used.

Outputs
-------
- reports/statistics/forest_fires_regression_results.csv
- reports/statistics/forest_fires_regression_summary.json
- reports/statistics/fires_best_model_predictions.csv
- reports/figures/regression_true_vs_pred_*.png
- exports/knime/forest_fires_regression_results.csv
- reports/practical_evidence/practical9_regression.md
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from python_src.config import settings
from python_src.logging_config import get_logger, setup_logging
from python_src.regression import run_fires_regression
from python_src.visualization import plot_regression_predictions

setup_logging()
logger = get_logger(__name__)


def main() -> int:
    settings.ensure_dirs()
    logger.info("=== Practical 9: Forest Fires Regression ===")

    fires_dir = settings.data_dir / "external"
    results = run_fires_regression(
        data_dir=fires_dir,
        out_dir=settings.statistics_dir,
        random_state=settings.random_seed,
        test_size=0.20,
    )

    if results.get("status") == "DATASET_NOT_AVAILABLE":
        logger.warning("Forest Fires dataset is not available: %s", results.get("message"))
        # Create an informative documentation file explaining how to acquire it
        md = f"""# Practical 9: Forest Fires Regression
*Status: Dataset Not Available Locally*

The UCI Forest Fires dataset is required for this practical.
Download from: https://archive.ics.uci.edu/dataset/162/forest+fires
Place the file at: `data/external/forestfires.csv`
Then rerun `python scripts/10_train_fires_regression.py`.
"""
        (settings.practical_evidence_dir / "practical9_regression.md").write_text(md, encoding="utf-8")
        return 0

    # If successful, plot predictions
    pred_path = settings.statistics_dir / "fires_best_model_predictions.csv"
    if pred_path.exists():
        preds_df = pd.read_csv(pred_path)
        plot_regression_predictions(
            y_true=preds_df["y_true_log"].values,
            y_pred=preds_df["y_pred_log"].values,
            model_name=results["best_model"],
            out_dir=settings.figures_dir,
        )

    # Copy regression results to KNIME exports
    src_res = settings.statistics_dir / "forest_fires_regression_results.csv"
    dst_res = settings.knime_exports_dir / "forest_fires_regression_results.csv"
    if src_res.exists():
        shutil.copy2(src_res, dst_res)
        logger.info("Exported regression results to %s", dst_res)

    # Generate practical evidence report
    metrics_path = settings.statistics_dir / "forest_fires_regression_results.csv"
    metrics_df = pd.read_csv(metrics_path) if metrics_path.exists() else pd.DataFrame()

    md = f"""# Practical 9: Forest Fires Regression Report
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Dataset Overview
- **Dataset**: UCI Forest Fires (Montesinho Natural Park, Portugal)
- **Observations**: {results.get('n_rows', 517)}
- **Zero-Area Fires**: {results.get('n_zeros_in_target', 247)}
- **Target Transformation**: `y = log1p(area)` to handle extreme right skewness

## Regression Model Evaluation (Test Set)
{metrics_df.to_markdown(index=False) if hasattr(metrics_df, 'to_markdown') else metrics_df.to_string()}

## Best Performing Model: {results.get('best_model', 'N/A')}
- Evaluated on both log-transformed scale (MAE, RMSE, R²) and raw hectare scale.
- Feature set includes meteorological predictors: FFMC, DMC, DC, ISI, temp, RH, wind, rain, plus encoded month/day.

## Academic & Methodological Notes
Forest fire burned area is notoriously challenging to predict due to meteorological non-linearities and high percentage of small, quickly contained fires (zero-area recorded). The log1p transformation stabilizes variance and minimizes extreme prediction penalties.
"""
    evidence_path = settings.practical_evidence_dir / "practical9_regression.md"
    evidence_path.write_text(md, encoding="utf-8")
    logger.info("✓ Forest fires regression complete. Evidence written to %s", evidence_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
