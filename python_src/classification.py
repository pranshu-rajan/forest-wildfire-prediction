"""
Classification module: train, evaluate, and serialise classifiers.

Covers Practical 7: Decision Tree, Random Forest, KNN.
All pipelines are leakage-safe (fit only on train, evaluate on held-out test).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from python_src.logging_config import get_logger
from python_src.schemas import COVER_TYPE_NAMES, TARGET_CLASSES

logger = get_logger(__name__)

CLASS_NAMES = [COVER_TYPE_NAMES[i] for i in TARGET_CLASSES]


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------

def get_classifiers(random_state: int = 42) -> dict[str, Pipeline]:
    """Return a dict of classifier name → sklearn Pipeline."""
    return {
        "Decision Tree": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", DecisionTreeClassifier(
                max_depth=20,
                min_samples_leaf=5,
                class_weight="balanced",
                random_state=random_state,
            )),
        ]),
        "Random Forest": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(
                n_estimators=200,
                max_depth=None,
                min_samples_leaf=2,
                n_jobs=-1,
                class_weight="balanced",
                random_state=random_state,
            )),
        ]),
        "KNN": Pipeline([
            ("scaler", StandardScaler()),
            ("clf", KNeighborsClassifier(
                n_neighbors=7,
                weights="distance",
                n_jobs=-1,
            )),
        ]),
    }


# ---------------------------------------------------------------------------
# Training and evaluation
# ---------------------------------------------------------------------------

def train_classifier(
    name: str,
    pipeline: Pipeline,
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> tuple[Pipeline, float]:
    """Fit a classifier pipeline on training data. Returns (fitted_pipeline, train_time_s)."""
    t0 = time.perf_counter()
    pipeline.fit(X_train, y_train)
    elapsed = time.perf_counter() - t0
    logger.info("Trained '%s' in %.1f s.", name, elapsed)
    return pipeline, elapsed


def evaluate_classifier(
    name: str,
    pipeline: Pipeline,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> dict[str, Any]:
    """Evaluate a fitted pipeline on the held-out test set."""
    from sklearn.metrics import (
        accuracy_score,
        balanced_accuracy_score,
        classification_report,
        confusion_matrix,
        f1_score,
    )

    t0 = time.perf_counter()
    y_pred = pipeline.predict(X_test)
    inference_time = time.perf_counter() - t0

    report_dict = classification_report(
        y_test, y_pred, target_names=CLASS_NAMES, output_dict=True, zero_division=0
    )

    cm = confusion_matrix(y_test, y_pred, labels=TARGET_CLASSES)

    result: dict[str, Any] = {
        "model": name,
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_test, y_pred)), 4),
        "macro_f1": round(float(f1_score(y_test, y_pred, average="macro", zero_division=0)), 4),
        "weighted_f1": round(float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 4),
        "inference_time_s": round(inference_time, 4),
        "per_class": {
            COVER_TYPE_NAMES[i]: {
                "precision": round(report_dict.get(COVER_TYPE_NAMES[i], {}).get("precision", 0.0), 4),
                "recall": round(report_dict.get(COVER_TYPE_NAMES[i], {}).get("recall", 0.0), 4),
                "f1": round(report_dict.get(COVER_TYPE_NAMES[i], {}).get("f1-score", 0.0), 4),
                "support": int(report_dict.get(COVER_TYPE_NAMES[i], {}).get("support", 0)),
            }
            for i in TARGET_CLASSES
        },
        "confusion_matrix": cm.tolist(),
    }
    logger.info(
        "Evaluated '%s': accuracy=%.4f, macro_f1=%.4f.",
        name, result["accuracy"], result["macro_f1"],
    )
    return result


def cross_validate_classifier(
    name: str,
    pipeline: Pipeline,
    X: np.ndarray,
    y: np.ndarray,
    cv: int = 5,
    seed: int = 42,
) -> dict[str, Any]:
    """Run stratified k-fold cross-validation."""
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=seed)
    cv_results = cross_validate(
        pipeline, X, y,
        cv=skf,
        scoring=["accuracy", "balanced_accuracy", "f1_macro", "f1_weighted"],
        return_train_score=False,
        n_jobs=-1,
    )
    result = {
        "model": name,
        "cv_folds": cv,
        "cv_accuracy_mean": round(float(cv_results["test_accuracy"].mean()), 4),
        "cv_accuracy_std": round(float(cv_results["test_accuracy"].std()), 4),
        "cv_balanced_accuracy_mean": round(float(cv_results["test_balanced_accuracy"].mean()), 4),
        "cv_macro_f1_mean": round(float(cv_results["test_f1_macro"].mean()), 4),
        "cv_weighted_f1_mean": round(float(cv_results["test_f1_weighted"].mean()), 4),
    }
    logger.info(
        "CV '%s': accuracy=%.4f ± %.4f.",
        name, result["cv_accuracy_mean"], result["cv_accuracy_std"],
    )
    return result


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def save_model(
    pipeline: Pipeline,
    name: str,
    out_dir: Path,
    metadata: dict[str, Any] | None = None,
) -> Path:
    """Serialise a fitted pipeline with joblib."""
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_name = name.lower().replace(" ", "_")
    model_path = out_dir / f"{safe_name}.joblib"
    joblib.dump(pipeline, model_path)
    logger.info("Model '%s' saved to %s.", name, model_path)

    if metadata:
        meta_path = out_dir / f"{safe_name}_metadata.json"
        with open(meta_path, "w") as fh:
            json.dump(metadata, fh, indent=2)

    return model_path


def load_model(path: Path) -> Pipeline:
    """Load a serialised model pipeline."""
    pipeline = joblib.load(path)
    logger.info("Model loaded from %s.", path)
    return pipeline


def train_and_evaluate_all(
    X_train: np.ndarray,
    X_test: np.ndarray,
    y_train: np.ndarray,
    y_test: np.ndarray,
    out_dir: Path,
    random_state: int = 42,
    run_cv: bool = True,
    cv_sample_n: int | None = 50_000,
    feature_names: list[str] | None = None,
) -> tuple[list[dict], list[dict]]:
    """Train, evaluate, and save all classifiers. Returns (metrics_list, cv_list)."""
    classifiers = get_classifiers(random_state=random_state)
    metrics_list: list[dict] = []
    cv_list: list[dict] = []

    for name, pipeline in classifiers.items():
        fitted, train_time = train_classifier(name, pipeline, X_train, y_train)
        result = evaluate_classifier(name, fitted, X_test, y_test)
        result["train_time_s"] = round(train_time, 2)

        meta = {
            "model_name": name,
            "random_state": random_state,
            "n_train": int(len(y_train)),
            "n_test": int(len(y_test)),
            "feature_names": feature_names or [],
            **{k: v for k, v in result.items() if k not in ("confusion_matrix", "per_class")},
        }
        save_model(fitted, name, out_dir, metadata=meta)
        metrics_list.append(result)

        if run_cv:
            # CV on a subset to avoid very long runtimes on 581k rows
            cv_X = X_train
            cv_y = y_train
            if cv_sample_n and len(X_train) > cv_sample_n:
                rng = np.random.default_rng(random_state)
                idx = rng.choice(len(X_train), size=cv_sample_n, replace=False)
                cv_X = X_train[idx]
                cv_y = y_train[idx]
                logger.info("CV for '%s' using %d-sample subset.", name, cv_sample_n)
            cv_result = cross_validate_classifier(name, pipeline, cv_X, cv_y, seed=random_state)
            cv_list.append(cv_result)

    return metrics_list, cv_list


def build_metrics_dataframe(metrics_list: list[dict]) -> pd.DataFrame:
    """Flatten per-model metric dicts into a summary DataFrame."""
    rows = []
    for m in metrics_list:
        rows.append(
            {
                "model": m["model"],
                "accuracy": m["accuracy"],
                "balanced_accuracy": m["balanced_accuracy"],
                "macro_f1": m["macro_f1"],
                "weighted_f1": m["weighted_f1"],
                "train_time_s": m.get("train_time_s", ""),
                "inference_time_s": m.get("inference_time_s", ""),
            }
        )
    return pd.DataFrame(rows)
