"""
Script 05: Descriptive statistics (Practical 3).

Computes and saves the full descriptive statistics table with formulas,
five-number summary, frequency distributions, and interpretation text.

Outputs
-------
- reports/statistics/descriptive_statistics.csv
- reports/statistics/five_number_summary.csv
- reports/statistics/frequency_distributions.json
- reports/practical_evidence/practical3_descriptive_stats.md
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
    descriptive_statistics,
    five_number_summary,
    frequency_distributions,
)

setup_logging()
logger = get_logger(__name__)


FORMULAS_MD = """
## Statistical Formulas

| Statistic | Formula |
|-----------|---------|
| Mean | $\\bar{x} = \\frac{1}{n}\\sum_{i=1}^{n} x_i$ |
| Median | Middle value of sorted data |
| Mode | Most frequent value |
| Midrange | $\\frac{x_{\\min} + x_{\\max}}{2}$ |
| Range | $x_{\\max} - x_{\\min}$ |
| Q1 | 25th percentile |
| Q3 | 75th percentile |
| IQR | $Q_3 - Q_1$ |
| Variance | $s^2 = \\frac{1}{n-1}\\sum_{i=1}^{n}(x_i - \\bar{x})^2$ |
| Std Dev | $s = \\sqrt{s^2}$ |
| Skewness | $\\frac{n}{(n-1)(n-2)}\\sum\\left(\\frac{x_i-\\bar{x}}{s}\\right)^3$ |
"""


def main() -> int:
    settings.ensure_dirs()
    logger.info("=== Practical 3: Descriptive Statistics ===")

    df = load_raw_covtype(settings.raw_covtype, add_record_id=True)

    # 1. Full descriptive statistics
    stats_df = descriptive_statistics(df)
    stats_df.to_csv(settings.statistics_dir / "descriptive_statistics.csv", index=False)
    logger.info("Descriptive statistics saved (%d features).", len(stats_df))

    # 2. Five-number summary
    fns = five_number_summary(df)
    fns.to_csv(settings.statistics_dir / "five_number_summary.csv", index=False)

    # 3. Frequency distributions
    freq = frequency_distributions(df)
    freq_dict = {}
    for key, series in freq.items():
        if hasattr(series, "to_dict"):
            freq_dict[key] = {str(k): int(v) for k, v in series.items()}
    with open(settings.statistics_dir / "frequency_distributions.json", "w") as fh:
        json.dump(freq_dict, fh, indent=2)

    # 4. Practical 3 evidence markdown
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Practical 3: Descriptive Statistics Report",
        f"*Generated: {ts}*",
        "",
        "## Purpose",
        "This report fulfils the Practical 3 requirement to compute and interpret",
        "descriptive statistics for the Covertype dataset's continuous features.",
        "",
        FORMULAS_MD,
        "",
        "## Results Table",
        "",
        stats_df.to_markdown(index=False) if hasattr(stats_df, "to_markdown") else stats_df.to_string(),
        "",
        "## Five-Number Summary",
        "",
        fns.to_markdown(index=False) if hasattr(fns, "to_markdown") else fns.to_string(),
        "",
        "## Sample Interpretation: Elevation",
    ]

    el = stats_df[stats_df["feature"] == "Elevation"]
    if not el.empty:
        r = el.iloc[0]
        lines += [
            f"- **Mean:** {r['mean']:,.1f} m — the average elevation across all {int(r['count']):,} observations.",
            f"- **Median:** {r['median']:,.1f} m — 50% of observations lie below this elevation.",
            f"- **Std Dev:** {r['std_dev']:,.1f} m — moderate spread indicating varied terrain.",
            f"- **IQR:** {r['iqr']:,.1f} m — the middle 50% spans {r['iqr']:,.0f} metres.",
            f"- **Skewness:** {r['skewness']:.3f} — {'approximately symmetric' if abs(r['skewness']) < 0.5 else 'moderately skewed'}.",
        ]

    content = "\n".join(lines)
    (settings.practical_evidence_dir / "practical3_descriptive_stats.md").write_text(content, encoding="utf-8")
    logger.info("Practical 3 evidence saved.")

    logger.info("✓ Descriptive statistics complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
