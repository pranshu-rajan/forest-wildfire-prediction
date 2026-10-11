"""
Script 06: Preprocessing experiments (Practical 10).

Demonstrates and compares:
- Smoothing (1-D local averaging)
- Min-max normalisation
- Z-score standardisation
- Pearson correlation
- Chi-square feature scoring
- Discretisation (quantile binning)
- Redundancy analysis

Outputs
-------
- reports/statistics/preprocessing_comparison.csv
- reports/statistics/pearson_correlation.csv
- reports/statistics/chi2_scores.csv
- reports/statistics/anova_f_scores.csv
- reports/statistics/redundancy_report.csv
- reports/practical_evidence/practical10_preprocessing.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python_src.config import settings
from python_src.ingestion import load_raw_covtype
from python_src.logging_config import get_logger, setup_logging
from python_src.preprocessing import compare_preprocessing_effects, discretise_continuous_features, stratified_split
from python_src.statistics import (
    pearson_correlation_matrix,
    chi2_feature_scores,
    high_correlations,
    redundancy_analysis,
    anova_f_scores,
)

setup_logging()
logger = get_logger(__name__)


def main() -> int:
    settings.ensure_dirs()
    logger.info("=== Practical 10: Preprocessing Experiments ===")

    df = load_raw_covtype(settings.raw_covtype, add_record_id=True)

    # 1. Preprocessing comparison (raw vs normalised vs standardised)
    preproc_results = compare_preprocessing_effects(df, sample_n=10_000, seed=settings.random_seed)
    rows = []
    for label, frame in preproc_results.items():
        desc = frame.describe().T
        desc["method"] = label
        desc = desc.reset_index().rename(columns={"index": "feature"})
        rows.append(desc)

    import pandas as pd
    comparison_df = pd.concat(rows, ignore_index=True)
    comparison_df.to_csv(settings.statistics_dir / "preprocessing_comparison.csv", index=False)
    logger.info("Preprocessing comparison saved.")

    # 2. Pearson correlation
    corr = pearson_correlation_matrix(df)
    corr.to_csv(settings.statistics_dir / "pearson_correlation.csv")

    high_corr = high_correlations(corr, threshold=0.75)
    high_corr.to_csv(settings.statistics_dir / "high_correlation_pairs.csv", index=False)
    logger.info("Found %d highly correlated pairs.", len(high_corr))

    # 3. Chi-square scores
    chi2_df = chi2_feature_scores(df, sample_n=50_000, seed=settings.random_seed)
    chi2_df.to_csv(settings.statistics_dir / "chi2_scores.csv", index=False)
    logger.info("Chi-square scores saved.")

    # 4. ANOVA F-scores
    anova_df = anova_f_scores(df, sample_n=50_000, seed=settings.random_seed)
    anova_df.to_csv(settings.statistics_dir / "anova_f_scores.csv", index=False)

    # 5. Redundancy analysis
    redundant = redundancy_analysis(corr, threshold=0.90)
    pd.DataFrame({"redundant_feature": redundant}).to_csv(
        settings.statistics_dir / "redundancy_report.csv", index=False
    )
    logger.info("Redundant features (r >= 0.90): %s", redundant)

    # 6. Discretisation
    disc_df, _ = discretise_continuous_features(df.sample(5000, random_state=42), n_bins=5, strategy="quantile")
    bin_cols = [c for c in disc_df.columns if c.endswith("_bin")]
    disc_df[bin_cols].describe().to_csv(settings.statistics_dir / "discretisation_summary.csv")
    logger.info("Discretisation summary saved.")

    # 7. Practical 10 evidence markdown
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md_lines = [
        "# Practical 10: Data Preprocessing Report",
        f"*Generated: {ts}*",
        "",
        "## 1. Smoothing",
        "Local 1-D mean smoothing (window=5) applied to continuous features via `GaussianSmoother`",
        "in `python_src/preprocessing.py`. Reduces micro-noise while preserving overall distribution shape.",
        "",
        "## 2. Normalisation (Min-Max Scaling)",
        "Scales each feature to [0, 1] using: x' = (x - min) / (max - min).",
        "Fit on training data only. Required for distance-based algorithms (KNN).",
        "",
        "## 3. Standardisation (Z-Score)",
        "Scales to mean=0, std=1 using: z = (x - μ) / σ.",
        "Fit on training data only. Required for PCA and regularised models.",
        "",
        "## 4. Pearson Correlation",
        "Pearson r measures linear association between two continuous variables.",
        "Formula: r = Σ[(xi - x̄)(yi - ȳ)] / √[Σ(xi - x̄)² × Σ(yi - ȳ)²]",
        "",
        f"High-correlation pairs (|r| > 0.75): {len(high_corr)} pairs found.",
        "",
        "## 5. Chi-Square Feature Selection",
        "χ² tests independence between a feature and the target class.",
        "Non-negative representation required — continuous features min-max scaled to [0,1].",
        "Chi-square is appropriate for categorical or discretised targets.",
        f"Top chi-square feature: **{chi2_df.iloc[0]['feature']}** (χ²={chi2_df.iloc[0]['chi2_score']:.1f})",
        "",
        "## 6. Discretisation",
        "Quantile binning (5 equal-frequency bins) converts continuous features into ordinal bins.",
        "Useful for rule-based systems and reducing impact of extreme outliers.",
        "",
        "## 7. Redundancy Analysis",
        f"Greedy correlation-based removal: {len(redundant)} features flagged as redundant (r ≥ 0.90).",
        f"Flagged: {redundant}",
    ]
    (settings.practical_evidence_dir / "practical10_preprocessing.md").write_text(
        "\n".join(md_lines), encoding="utf-8"
    )
    logger.info("✓ Preprocessing experiments complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
