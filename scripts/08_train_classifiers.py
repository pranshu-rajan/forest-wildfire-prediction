"""
Script 08: Train and evaluate classifiers (Practical 7).

Models: Decision Tree, Random Forest, K-Nearest Neighbors
Evaluation: accuracy, balanced accuracy, macro/weighted F1, confusion matrix, cross-validation.

Outputs
-------
- models/decision_tree.joblib
- models/random_forest.joblib
- models/knn.joblib
- reports/statistics/classification_metrics.json
- reports/statistics/classification_metrics_summary.csv
- reports/statistics/cv_results.csv
- reports/figures/confusion_matrix_*.png
- reports/figures/model_comparison.png
- reports/figures/feature_importance_random_forest.png
- exports/knime/classification_metrics.csv
- exports/knime/prediction_results.csv
- reports/practical_evidence/practical7_classification.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from python_src.config import settings
from python_src.ingestion import load_raw_covtype
from python_src.logging_config import get_logger, setup_logging
from python_src.preprocessing import stratified_split, save_split_indices
from python_src.classification import train_and_evaluate_all, build_metrics_dataframe
from python_src.visualization import (
    plot_confusion_matrix,
    plot_model_comparison,
    plot_feature_importance,
)
from python_src.schemas import ALL_FEATURES, COVER_TYPE_NAMES, TARGET_CLASSES

setup_logging()
logger = get_logger(__name__)


def main() -> int:
    settings.ensure_dirs()
    logger.info("=== Practical 7: Classification ===")

    df = load_raw_covtype(settings.raw_covtype, add_record_id=True)
    feature_cols = [c for c in ALL_FEATURES if c in df.columns]

    X_train, X_test, y_train, y_test = stratified_split(
        df,
        test_size=settings.test_size,
        random_seed=settings.random_seed,
        feature_cols=feature_cols,
    )
    save_split_indices(X_train.index, X_test.index, settings.models_dir)

    X_train_arr = X_train.values
    X_test_arr = X_test.values

    logger.info("Train: %d | Test: %d | Features: %d", len(y_train), len(y_test), len(feature_cols))

    # Train all models (CV on 50k sample for speed)
    metrics_list, cv_list = train_and_evaluate_all(
        X_train_arr, X_test_arr, y_train, y_test,
        out_dir=settings.models_dir,
        random_state=settings.random_seed,
        run_cv=True,
        cv_sample_n=50_000,
        feature_names=feature_cols,
    )

    # Save metrics JSON
    with open(settings.statistics_dir / "classification_metrics.json", "w") as fh:
        # Remove confusion matrix from JSON for readability (it's saved separately)
        clean_metrics = [{k: v for k, v in m.items() if k != "confusion_matrix"} for m in metrics_list]
        json.dump({"metrics": clean_metrics, "cv_results": cv_list}, fh, indent=2)

    # Summary CSV
    metrics_df = build_metrics_dataframe(metrics_list)
    metrics_df.to_csv(settings.statistics_dir / "classification_metrics_summary.csv", index=False)
    metrics_df.to_csv(settings.knime_exports_dir / "classification_metrics.csv", index=False)

    # CV results CSV
    pd.DataFrame(cv_list).to_csv(settings.statistics_dir / "cv_results.csv", index=False)

    # Confusion matrices and prediction exports
    class_names = [COVER_TYPE_NAMES[i] for i in TARGET_CLASSES]
    best_preds = None
    best_acc = 0.0

    for m in metrics_list:
        cm = np.array(m["confusion_matrix"])
        plot_confusion_matrix(cm, class_names, m["model"], settings.figures_dir)
        if m["accuracy"] > best_acc:
            best_acc = m["accuracy"]
            # Reconstruct predictions from best model
            import joblib
            safe_name = m["model"].lower().replace(" ", "_")
            model_path = settings.models_dir / f"{safe_name}.joblib"
            if model_path.exists():
                pipeline = joblib.load(model_path)
                best_preds = pipeline.predict(X_test_arr)

    # Export prediction results for KNIME
    if best_preds is not None:
        from python_src.exports import export_prediction_results
        export_prediction_results(y_test, best_preds, settings.knime_exports_dir)

    # Model comparison chart
    plot_model_comparison(
        metrics_df,
        metric_cols=["accuracy", "balanced_accuracy", "macro_f1", "weighted_f1"],
        out_dir=settings.figures_dir,
    )

    # Feature importance (Random Forest)
    rf_path = settings.models_dir / "random_forest.joblib"
    if rf_path.exists():
        import joblib
        rf_pipeline = joblib.load(rf_path)
        importances = rf_pipeline.named_steps["clf"].feature_importances_
        plot_feature_importance(importances, feature_cols, "Random Forest", settings.figures_dir)

    # Practical 7 evidence
    from datetime import datetime
    best_model = metrics_df.sort_values("accuracy", ascending=False).iloc[0]
    md = f"""# Practical 7: Classification Report
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

## Models Trained
- Decision Tree (max_depth=20, balanced class weights)
- Random Forest (200 trees, balanced class weights)
- K-Nearest Neighbors (k=7, distance weighting)

## Test Set Results
{metrics_df.to_markdown(index=False) if hasattr(metrics_df, 'to_markdown') else metrics_df.to_string()}

## Cross-Validation Results (50k-sample subset, 5-fold)
{pd.DataFrame(cv_list).to_markdown(index=False) if cv_list else 'N/A'}

## Best Model: {best_model['model']}
- Test Accuracy: **{best_model['accuracy']:.4f}**
- Balanced Accuracy: **{best_model['balanced_accuracy']:.4f}**
- Macro F1: **{best_model['macro_f1']:.4f}**

## Notes on Class Imbalance
The Covertype dataset has significant class imbalance (classes 1 and 2 dominate).
Balanced class weights were used in tree-based models. Balanced accuracy provides
a fairer evaluation metric than plain accuracy for imbalanced datasets.
"""
    (settings.practical_evidence_dir / "practical7_classification.md").write_text(md, encoding="utf-8")

    logger.info("✓ Classification complete. Best: %s (acc=%.4f)", best_model["model"], best_model["accuracy"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
