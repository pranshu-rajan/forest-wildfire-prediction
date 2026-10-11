"""
Script 03: Synthetic missing-value cleaning demonstration (Practical 2).

This script creates a fully reproducible controlled experiment demonstrating
the missing-value imputation pipeline. The original source CSV is NEVER modified.

Expected outcomes:
  - Demo sample: 10,000 rows
  - Injected missing cells: exactly 800
  - Missing cells after cleaning: 0
  - Row count preserved: True
  - Target labels unchanged: True

Outputs
-------
- data/processed/covtype_missing_values_demo.csv  (corrupted teaching copy)
- data/processed/covtype_missing_values_demo_clean.csv  (median-imputed copy)
- reports/data_quality/synthetic_demo_before.csv
- reports/data_quality/synthetic_demo_after.csv
- reports/data_quality/synthetic_demo_audit.json
- reports/data_quality/synthetic_demo_report.md
- reports/figures/missing_value_heatmap_before.png
- reports/figures/missing_value_heatmap_after.png
- reports/figures/synthetic_cleaning_before_after.png
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python_src.config import settings
from python_src.ingestion import load_raw_covtype
from python_src.logging_config import get_logger, setup_logging
from python_src.synthetic_data import (
    apply_median_imputation,
    build_quality_snapshot,
    generate_markdown_report,
    inject_missing_values,
    sample_from_covtype,
    validate_cleaning_result,
)
from python_src.visualization import (
    plot_before_after_imputation,
    plot_missing_heatmap,
)

setup_logging()
logger = get_logger(__name__)

N_ROWS = settings.synthetic_missing_demo_rows  # 10,000
N_INJECT = 800
SEED = 42
INJECTION_SEED = 2024


def main() -> int:
    settings.ensure_dirs()
    logger.info("=== Practical 2: Synthetic Missing-Value Cleaning Experiment ===")
    logger.info("N_ROWS=%d | N_INJECT=%d | SEED=%d | INJECTION_SEED=%d", N_ROWS, N_INJECT, SEED, INJECTION_SEED)

    # 1. Load full dataset
    path = settings.raw_covtype
    if not path.exists():
        logger.error("Dataset not found: %s", path)
        return 1

    full_df = load_raw_covtype(path, add_record_id=True)
    logger.info("Full dataset loaded: %d rows.", len(full_df))

    # 2. Sample baseline (clean copy)
    baseline = sample_from_covtype(full_df, n_rows=N_ROWS, seed=SEED)
    baseline.to_csv(settings.processed_data_dir / "covtype_demo_baseline.csv", index=False)
    logger.info("Baseline copy saved (%d rows).", len(baseline))

    # 3. Inject exactly 800 missing values
    corrupted, injection_record = inject_missing_values(
        baseline, n_inject=N_INJECT, seed=INJECTION_SEED
    )
    corrupted.to_csv(settings.demo_raw_path, index=False)
    logger.info("Corrupted demo saved: %s", settings.demo_raw_path)

    # 4. Before-cleaning quality snapshot
    from python_src.schemas import CONTINUOUS_FEATURES
    cont_cols = [c for c in CONTINUOUS_FEATURES if c in corrupted.columns]
    before_snapshot = build_quality_snapshot(corrupted, columns=cont_cols)
    before_snapshot.to_csv(settings.data_quality_dir / "synthetic_demo_before.csv", index=False)

    # 5. Apply median imputation
    cleaned, imputation_audit = apply_median_imputation(corrupted, columns=cont_cols)
    cleaned.to_csv(settings.demo_clean_path, index=False)
    logger.info("Cleaned demo saved: %s", settings.demo_clean_path)

    # 6. After-cleaning quality snapshot
    after_snapshot = build_quality_snapshot(cleaned, columns=cont_cols)
    after_snapshot.to_csv(settings.data_quality_dir / "synthetic_demo_after.csv", index=False)

    # 7. Validate outcomes
    checks = validate_cleaning_result(
        baseline=baseline,
        corrupted=corrupted,
        cleaned=cleaned,
        injection_record=injection_record,
        columns=cont_cols,
    )

    # 8. Save JSON audit
    audit_dict = {
        "experiment_parameters": {
            "n_rows": N_ROWS,
            "n_injected": N_INJECT,
            "seed": SEED,
            "injection_seed": INJECTION_SEED,
        },
        "injection_record": injection_record.to_list()[:20],  # first 20 for brevity
        "imputation_audit": imputation_audit.to_dict(),
        "validation_checks": checks,
    }
    with open(settings.data_quality_dir / "synthetic_demo_audit.json", "w") as fh:
        json.dump(audit_dict, fh, indent=2)

    # 9. Markdown report
    md = generate_markdown_report(checks, injection_record, imputation_audit, N_ROWS)
    (settings.data_quality_dir / "synthetic_demo_report.md").write_text(md, encoding="utf-8")
    logger.info("Markdown report saved.")

    # 10. Visualisations
    plot_missing_heatmap(
        corrupted, settings.figures_dir,
        title="Missing Value Heatmap — Before Cleaning [Synthetic Demo]",
        filename="missing_value_heatmap_before.png",
    )
    plot_missing_heatmap(
        cleaned, settings.figures_dir,
        title="Missing Value Heatmap — After Cleaning [Synthetic Demo]",
        filename="missing_value_heatmap_after.png",
    )
    plot_before_after_imputation(before_snapshot, after_snapshot, settings.figures_dir)

    # 11. Final summary
    all_passed = checks.get("all_checks_passed", False)
    logger.info(
        "Experiment complete. All checks passed: %s",
        "YES ✓" if all_passed else "NO ✗ — review audit log",
    )

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
