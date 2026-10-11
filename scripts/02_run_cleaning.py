"""
Script 02: Real-data cleaning pipeline.

Applies the cleaning pipeline to the validated Covertype dataset:
- Flags IQR and z-score outliers (no rows deleted)
- Saves the cleaned Parquet to data/processed/
- Saves before/after quality reports and outlier comparison

Outputs
-------
- data/processed/covtype_clean.parquet
- reports/data_quality/data_quality_after.csv
- reports/data_quality/outlier_comparison.csv
- reports/data_quality/cleaning_log.json
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python_src.config import settings
from python_src.ingestion import load_raw_covtype
from python_src.logging_config import get_logger, setup_logging
from python_src.cleaning import clean_covtype, build_outlier_comparison, generate_quality_report

setup_logging()
logger = get_logger(__name__)


def main() -> int:
    settings.ensure_dirs()
    logger.info("=== Phase 1: Real-Data Cleaning Pipeline ===")

    path = settings.raw_covtype
    if not path.exists():
        logger.error("Dataset not found: %s", path)
        return 1

    df = load_raw_covtype(path, add_record_id=True)
    logger.info("Loaded %d rows.", len(df))

    # Apply cleaning pipeline
    df_clean, log = clean_covtype(df, iqr_multiplier=settings.iqr_multiplier, zscore_threshold=settings.zscore_threshold)

    # Save cleaning log
    log.save(settings.data_quality_dir / "cleaning_log.json")

    # Quality report after cleaning
    quality_after = generate_quality_report(df_clean, label="cleaned")
    quality_after.to_csv(settings.data_quality_dir / "data_quality_after.csv", index=False)

    # Outlier comparison
    outlier_df = build_outlier_comparison(df_clean)
    outlier_df.to_csv(settings.data_quality_dir / "outlier_comparison.csv", index=False)
    logger.info("Outlier comparison saved.")

    # Save processed Parquet (without outlier flag columns to keep it clean)
    core_cols = [c for c in df_clean.columns if not ("_iqr_outlier" in c or "_zscore_outlier" in c)]
    df_export = df_clean[core_cols]
    try:
        df_export.to_parquet(settings.processed_covtype, index=False)
        logger.info("Cleaned dataset saved to %s (%d rows).", settings.processed_covtype, len(df_export))
    except Exception as exc:
        csv_path = settings.processed_covtype.with_suffix(".csv")
        df_export.to_csv(csv_path, index=False)
        logger.warning("Parquet save failed (%s). Saved CSV fallback to %s.", exc, csv_path)

    logger.info("✓ Cleaning pipeline complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
