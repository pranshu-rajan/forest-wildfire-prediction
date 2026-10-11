"""
Reporting module: generate Markdown and JSON reports from computed outputs.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from python_src.logging_config import get_logger
from python_src.schemas import COVER_TYPE_NAMES

logger = get_logger(__name__)


def generate_eda_report(
    summary: dict[str, Any],
    stats_df: pd.DataFrame,
    out_dir: Path,
) -> Path:
    """Generate a Markdown EDA report from computed outputs."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dist = summary.get("class_distribution", {})

    lines = [
        "# Exploratory Data Analysis Report",
        f"*Generated: {ts}*",
        "",
        "## Dataset Overview",
        f"- **Rows:** {summary['n_rows']:,}",
        f"- **Columns:** {summary['n_columns']}",
        f"- **Continuous features:** {summary['n_continuous_features']}",
        f"- **Binary features:** {summary['n_binary_features']}",
        f"- **Total missing cells:** {summary['n_missing_total']}",
        f"- **Duplicate rows:** {summary['n_duplicate_rows']:,}",
        f"- **Memory usage:** {summary['memory_mb']} MB",
        "",
        "## Class Distribution (Cover_Type)",
        "| Class | Name | Count | % |",
        "|-------|------|-------|---|",
    ]
    for ct_id, info in dist.items():
        lines.append(f"| {ct_id} | {info['name']} | {info['count']:,} | {info['pct']}% |")

    lines += [
        "",
        "## Descriptive Statistics (Continuous Features)",
        "",
        stats_df.to_markdown(index=False) if hasattr(stats_df, "to_markdown") else stats_df.to_string(),
        "",
        "## Key Observations",
        "- The dataset has **no missing values** in the original source.",
        "- Class imbalance is present: classes 1 (Spruce/Fir) and 2 (Lodgepole Pine) dominate.",
        "- Hillshade features (9am, Noon, 3pm) show moderate inter-correlation.",
        "- Many soil type columns are sparse (< 1% activation).",
        "",
        "## Figures Generated",
        "- `reports/figures/class_distribution_bar.png`",
        "- `reports/figures/class_distribution_pie.png`",
        "- `reports/figures/continuous_distributions.png`",
        "- `reports/figures/boxplots_by_cover_type.png`",
        "- `reports/figures/correlation_heatmap.png`",
        "- `reports/figures/scatter_elevation_vs_hydrology.png`",
        "- `reports/figures/wilderness_area_distribution.png`",
        "- `reports/figures/soil_type_frequency.png`",
        "- `reports/figures/treemap_cover_type.png`",
        "- `reports/figures/radial_cover_distribution.png`",
    ]

    content = "\n".join(lines)
    path = out_dir / "eda_report.md"
    path.write_text(content, encoding="utf-8")
    logger.info("EDA report saved to %s.", path)
    return path


def generate_audit_report(
    validation_report: dict,
    cleaning_log: dict,
    manifest: dict,
    out_dir: Path,
) -> Path:
    """Generate a data audit Markdown report."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = validation_report.get("summary", {})

    lines = [
        "# Data Audit Report",
        f"*Generated: {ts}*",
        "",
        "## Source Manifest",
        f"- **File:** {manifest.get('source_path', 'N/A')}",
        f"- **SHA-256:** `{manifest.get('sha256', 'N/A')}`",
        f"- **Rows:** {manifest.get('row_count', 'N/A'):,}",
        f"- **Columns:** {manifest.get('column_count', 'N/A')}",
        f"- **Ingested at:** {manifest.get('ingested_at', 'N/A')}",
        "",
        "## Validation Summary",
        f"- Total checks: {summary.get('total_checks', '?')}",
        f"- Passed: {summary.get('passed', '?')}",
        f"- Fatal failures: {summary.get('fatal_failures', '?')}",
        f"- Warnings: {summary.get('warnings', '?')}",
        "",
        "## Validation Checks",
        "| Check | Passed | Severity | Detail |",
        "|-------|--------|----------|--------|",
    ]
    for check in validation_report.get("checks", []):
        icon = "✅" if check["passed"] else ("❌" if check["severity"] == "FATAL" else "⚠️")
        lines.append(
            f"| {check['check']} | {icon} | {check['severity']} | {check['detail'][:100]} |"
        )

    lines += [
        "",
        "## Cleaning Operations",
        "| Operation | Rows In | Rows Out | Rows Affected | Detail |",
        "|-----------|---------|----------|---------------|--------|",
    ]
    for op in cleaning_log.get("operations", []):
        lines.append(
            f"| {op['operation']} | {op['rows_in']:,} | {op['rows_out']:,} | "
            f"{op['rows_affected']:+,} | {op['details'][:80]} |"
        )

    content = "\n".join(lines)
    path = out_dir / "audit_report.md"
    path.write_text(content, encoding="utf-8")
    logger.info("Audit report saved to %s.", path)
    return path
