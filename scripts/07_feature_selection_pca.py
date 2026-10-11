"""
Script 07: Feature selection and PCA (Practical 6b, Unit IV).

Outputs
-------
- reports/statistics/feature_ranking_combined.csv
- reports/statistics/pca_report.json
- reports/statistics/pca_loadings.csv
- reports/figures/pca_explained_variance.png
- exports/knime/feature_selection_results.csv
- exports/knime/pca_scores.csv
- models/pca_scaler.joblib
- models/pca_model.joblib
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import joblib
import numpy as np

from python_src.config import settings
from python_src.ingestion import load_raw_covtype
from python_src.logging_config import get_logger, setup_logging
from python_src.preprocessing import stratified_split
from python_src.feature_selection import (
    combined_feature_ranking,
    variance_threshold_filter,
)
from python_src.dimensionality_reduction import (
    fit_pca_pipeline,
    pca_scores_dataframe,
    loadings_dataframe,
    pca_report,
)
from python_src.visualization import plot_pca_explained_variance
from python_src.schemas import ALL_FEATURES, CONTINUOUS_FEATURES, BINARY_FEATURES

setup_logging()
logger = get_logger(__name__)


def main() -> int:
    settings.ensure_dirs()
    logger.info("=== Practical 6b: Feature Selection and PCA ===")

    df = load_raw_covtype(settings.raw_covtype, add_record_id=True)

    feature_cols = [c for c in ALL_FEATURES if c in df.columns]
    X_train, X_test, y_train, y_test = stratified_split(
        df, test_size=settings.test_size,
        random_seed=settings.random_seed,
        feature_cols=feature_cols,
    )

    import pandas as pd
    X_train_arr = X_train.values if hasattr(X_train, "values") else X_train
    X_test_arr = X_test.values if hasattr(X_test, "values") else X_test

    # 1. Variance threshold (remove zero-variance binary cols)
    X_train_vt, kept_features, removed_features = variance_threshold_filter(
        X_train_arr, feature_cols, threshold=0.001
    )
    X_test_vt = X_test_arr[:, [feature_cols.index(f) for f in kept_features]]
    logger.info("After VarianceThreshold: %d features kept, %d removed.", len(kept_features), len(removed_features))

    # 2. Combined feature ranking (subsample for speed)
    sample_size = min(50_000, len(X_train_vt))
    rng = np.random.default_rng(settings.random_seed)
    idx = rng.choice(len(X_train_vt), size=sample_size, replace=False)
    ranking = combined_feature_ranking(
        X_train_vt[idx], y_train[idx], kept_features, seed=settings.random_seed
    )
    ranking.to_csv(settings.statistics_dir / "feature_ranking_combined.csv", index=False)
    ranking.to_csv(settings.knime_exports_dir / "feature_selection_results.csv", index=False)
    logger.info("Feature ranking saved.")

    # 3. PCA (95% variance threshold)
    # Use only continuous features for PCA (binary features distort PCA)
    cont_idx = [kept_features.index(f) for f in CONTINUOUS_FEATURES if f in kept_features]
    X_train_cont = X_train_vt[:, cont_idx]
    X_test_cont = X_test_vt[:, [kept_features.index(f) for f in CONTINUOUS_FEATURES if f in kept_features]]

    X_train_pca, X_test_pca, pca_obj, scaler_obj, pca_rep = fit_pca_pipeline(
        X_train_cont, X_test_cont,
        feature_names=[f for f in CONTINUOUS_FEATURES if f in kept_features],
        n_components=0.95,
        random_state=settings.random_seed,
    )

    # Save PCA report
    with open(settings.statistics_dir / "pca_report.json", "w") as fh:
        json.dump(pca_rep, fh, indent=2)
    logger.info(
        "PCA: %d continuous features → %d components (%.1f%% variance).",
        len(cont_idx), pca_rep["n_components"], pca_rep["total_explained_variance_pct"]
    )

    # Loadings
    cont_names = [f for f in CONTINUOUS_FEATURES if f in kept_features]
    loadings_df = loadings_dataframe(pca_obj, cont_names)
    loadings_df.to_csv(settings.statistics_dir / "pca_loadings.csv")

    # PCA scores for KNIME export (test set, first 50k)
    scores_df = pca_scores_dataframe(scaler_obj.transform(X_test_cont), pca_obj, n_components=min(10, pca_obj.n_components_))
    scores_df["Cover_Type"] = y_test[:len(scores_df)]
    scores_df.to_csv(settings.knime_exports_dir / "pca_scores.csv", index=False)

    # 4. Explained variance plot
    plot_pca_explained_variance(pca_obj.explained_variance_ratio_, settings.figures_dir)

    # 5. Save model artifacts
    joblib.dump(scaler_obj, settings.models_dir / "pca_scaler.joblib")
    joblib.dump(pca_obj, settings.models_dir / "pca_model.joblib")

    # 6. Practical evidence markdown
    from datetime import datetime
    md = f"""# Practical 6b: Feature Selection and PCA Report
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Feature Ranking Summary
- Total features: {len(feature_cols)}
- After variance threshold: {len(kept_features)}
- Removed (zero-variance): {removed_features}

### Top 10 Features by Mean Rank
{ranking.head(10).to_markdown(index=False) if hasattr(ranking, 'to_markdown') else ranking.head(10).to_string()}

## PCA Results (Continuous Features)
- Input features: {len(cont_idx)} continuous features
- Components retained: {pca_rep['n_components']} (for {pca_rep['total_explained_variance_pct']}% variance)
- Components for 90% variance: {pca_rep['n_components_for_90pct_variance']}
- Components for 95% variance: {pca_rep['n_components_for_95pct_variance']}

## PCA Limitations
- PCA is sensitive to feature scale — standardisation is mandatory first.
- PCA assumes linear relationships; non-linear structure may not be captured.
- Interpretability is reduced: each PC is a linear combination of all original features.
- The curse of dimensionality: with 54 features, distance-based methods can degrade.
  PCA mitigates this for the continuous subspace but cannot resolve binary feature sparsity.
"""
    (settings.practical_evidence_dir / "practical6b_feature_pca.md").write_text(md, encoding="utf-8")

    logger.info("✓ Feature selection and PCA complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
