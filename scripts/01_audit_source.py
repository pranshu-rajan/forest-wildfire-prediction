"""
Script 01: Source audit — validate, fingerprint, and profile the raw Covertype dataset.

Outputs
-------
- reports/data_quality/source_manifest.json
- reports/data_quality/validation_report.json
- reports/data_quality/audit_report.md
- reports/data_quality/data_quality_before.csv
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python_src.config import settings
from python_src.ingestion import build_source_manifest, load_raw_covtype, save_manifest
from python_src.logging_config import get_logger, setup_logging
from python_src.validation import validate_covtype
from python_src.cleaning import generate_quality_report
from python_src.reporting import generate_audit_report

setup_logging()
logger = get_logger(__name__)


def main() -> int:
    settings.ensure_dirs()
    logger.info("=== Phase 1: Source Audit ===")

    # 1. Load dataset
    path = settings.raw_covtype
    if not path.exists():
        logger.error("Dataset not found: %s", path)
        return 1

    df = load_raw_covtype(path, add_record_id=True)

    # 2. Build and save manifest
    manifest = build_source_manifest(path, df, settings.dataset_version)
    save_manifest(manifest, settings.data_quality_dir / "source_manifest.json")
    logger.info("SHA-256: %s", manifest["sha256"])

    # 3. Run validation
    report = validate_covtype(df, path)
    report.save(settings.data_quality_dir / "validation_report.json")

    # 4. Quality snapshot
    quality_df = generate_quality_report(df, label="raw")
    quality_df.to_csv(settings.data_quality_dir / "data_quality_before.csv", index=False)
    logger.info("Quality report: %d columns profiled.", len(quality_df))

    # 5. Markdown audit report
    generate_audit_report(
        report.to_dict(),
        {"operations": []},
        manifest,
        settings.data_quality_dir,
    )

    # 6. Summary
    logger.info(
        "Audit complete: %d rows, %d cols, %d fatal issues, %d warnings.",
        manifest["row_count"],
        manifest["column_count"],
        report.fatal_count,
        report.warning_count,
    )

    if report.fatal_count > 0:
        logger.error("FATAL validation failures detected. Review %s.", settings.data_quality_dir)
        return 1

    logger.info("✓ Source audit passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
