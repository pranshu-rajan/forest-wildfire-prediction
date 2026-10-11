"""
Evaluation utilities: shared metric computation and reporting helpers.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

from python_src.logging_config import get_logger
from python_src.schemas import COVER_TYPE_NAMES, TARGET_CLASSES

logger = get_logger(__name__)
CLASS_NAMES = [COVER_TYPE_NAMES[i] for i in TARGET_CLASSES]


def compute_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str = "Model",
) -> dict[str, Any]:
    """Compute a comprehensive set of classification metrics."""
    acc = float(accuracy_score(y_true, y_pred))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
    cm = confusion_matrix(y_true, y_pred, labels=TARGET_CLASSES)

    report = classification_report(
        y_true, y_pred, target_names=CLASS_NAMES, output_dict=True, zero_division=0
    )

    return {
        "model": model_name,
        "accuracy": round(acc, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
    }


def metrics_to_dataframe(metrics_list: list[dict]) -> pd.DataFrame:
    """Convert a list of metric dicts to a summary DataFrame."""
    rows = [
        {
            "model": m["model"],
            "accuracy": m.get("accuracy"),
            "balanced_accuracy": m.get("balanced_accuracy"),
            "macro_f1": m.get("macro_f1"),
            "weighted_f1": m.get("weighted_f1"),
        }
        for m in metrics_list
    ]
    return pd.DataFrame(rows)


def confusion_matrix_dataframe(cm: list[list[int]]) -> pd.DataFrame:
    """Convert a confusion matrix list to a labelled DataFrame."""
    return pd.DataFrame(
        cm,
        index=[f"True_{n}" for n in CLASS_NAMES],
        columns=[f"Pred_{n}" for n in CLASS_NAMES],
    )
