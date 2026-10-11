"""End-to-End Machine Learning Prediction Pipeline.

Provides production inference capabilities:
- Model Loading & Caching (Random Forest, Decision Tree, KNN)
- Feature Validation & Schema Alignment (54 predictors in strict order)
- Scaler Transformation & Estimator Evaluation
- Probability Calibration & Ecological Species Mapping
- Single-instance inference (`predict_single`)
- High-throughput batch inference (`predict_batch`)
- CLI command-line prediction interface
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import numpy as np
import pandas as pd

from python_src.config import settings
from python_src.logging_config import get_logger
from python_src.schemas import (
    ALL_FEATURES,
    CONTINUOUS_FEATURES,
    COVER_TYPE_NAMES,
    TARGET_CLASSES,
    WILDERNESS_FEATURES,
    SOIL_FEATURES,
)

logger = get_logger("ml_prediction_pipeline")

# In-memory model cache
_MODEL_CACHE: Dict[str, Any] = {}


def load_model_pipeline(model_name: str = "random_forest") -> Optional[Any]:
    """Load and cache serialized scikit-learn pipeline from models/ directory."""
    if model_name in _MODEL_CACHE:
        return _MODEL_CACHE[model_name]

    model_path = settings.models_dir / f"{model_name}.joblib"
    if not model_path.exists():
        # Fallback to alternate models
        for alt in ["random_forest", "decision_tree"]:
            alt_path = settings.models_dir / f"{alt}.joblib"
            if alt_path.exists():
                model_path = alt_path
                model_name = alt
                break

    if model_path.exists():
        try:
            model = joblib.load(model_path)
            _MODEL_CACHE[model_name] = model
            logger.info("Loaded ML model pipeline: %s", model_path)
            return model
        except Exception as exc:
            logger.error("Failed to load model pipeline from %s: %s", model_path, exc)

    return None


def validate_and_align_features(features: Dict[str, Union[int, float]]) -> tuple[np.ndarray, List[str]]:
    """Validate that features contain all required columns and align into exact schema order.

    Returns:
        tuple[np.ndarray, List[str]]: (1x54 feature matrix, list of missing feature names)
    """
    missing = []
    vector = []

    for col in ALL_FEATURES:
        if col in features:
            try:
                vector.append(float(features[col]))
            except (ValueError, TypeError):
                vector.append(0.0)
        else:
            missing.append(col)

    if missing:
        return np.empty((0, len(ALL_FEATURES))), missing

    return np.array([vector], dtype=np.float32), []


def predict_single(
    features: Dict[str, Union[int, float]],
    model_name: str = "random_forest",
) -> Dict[str, Any]:
    """Execute end-to-end ML prediction on a single feature dictionary.

    Args:
        features: Dictionary containing exactly all 54 feature values.
        model_name: Model pipeline identifier ('random_forest', 'decision_tree', 'knn').

    Returns:
        Dict containing predicted class, species name, confidence probabilities, and metadata.
    """
    t0 = time.perf_counter()
    X_in, missing = validate_and_align_features(features)

    if missing:
        raise ValueError(f"Incomplete feature payload. Missing {len(missing)} features: {missing[:5]}...")

    pipeline = load_model_pipeline(model_name)
    actual_model = model_name

    if pipeline is not None:
        pred_class = int(pipeline.predict(X_in)[0])
        probabilities = None
        if hasattr(pipeline, "predict_proba"):
            try:
                probs = pipeline.predict_proba(X_in)[0]
                classes = pipeline.classes_
                probabilities = {
                    COVER_TYPE_NAMES.get(int(c), f"Class {c}"): round(float(p), 4)
                    for c, p in zip(classes, probs)
                }
            except Exception:
                probabilities = None
    else:
        # Heuristic fallback if models not present
        actual_model = "ecological_heuristic"
        elev = float(features.get("Elevation", 2800))
        if elev > 3300:
            pred_class = 7
        elif elev > 3000:
            pred_class = 1
        elif elev > 2600:
            pred_class = 2
        elif elev < 2200:
            pred_class = 4
        elif elev < 2500:
            pred_class = 3
        else:
            pred_class = 2

        probabilities = {
            COVER_TYPE_NAMES[c]: 0.82 if c == pred_class else round(0.18 / 6, 3)
            for c in TARGET_CLASSES
        }

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    return {
        "predicted_cover_type": pred_class,
        "cover_name": COVER_TYPE_NAMES.get(pred_class, f"Class {pred_class}"),
        "probabilities": probabilities,
        "model_used": actual_model,
        "latency_ms": latency_ms,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def predict_batch(
    df: pd.DataFrame,
    model_name: str = "random_forest",
) -> pd.DataFrame:
    """Execute high-throughput batch prediction on a pandas DataFrame.

    Args:
        df: DataFrame containing the 54 predictor columns.
        model_name: Model pipeline identifier.

    Returns:
        pd.DataFrame with original features plus 'predicted_cover_type', 'cover_name', and max 'confidence'.
    """
    pipeline = load_model_pipeline(model_name)
    if pipeline is None:
        raise RuntimeError(f"Could not load ML pipeline '{model_name}'.")

    # Validate columns
    missing = [col for col in ALL_FEATURES if col not in df.columns]
    if missing:
        raise ValueError(f"DataFrame is missing {len(missing)} required columns: {missing[:5]}...")

    X = df[ALL_FEATURES].values.astype(np.float32)
    predictions = pipeline.predict(X)

    result_df = df.copy()
    result_df["predicted_cover_type"] = predictions.astype(int)
    result_df["cover_name"] = result_df["predicted_cover_type"].map(COVER_TYPE_NAMES)

    if hasattr(pipeline, "predict_proba"):
        try:
            probs = pipeline.predict_proba(X)
            result_df["prediction_confidence"] = np.max(probs, axis=1).round(4)
        except Exception:
            pass

    return result_df


# ---------------------------------------------------------------------------
# CLI Prediction Interface
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="End-to-End ML Prediction Pipeline CLI")
    parser.add_argument("--model", default="random_forest", choices=["random_forest", "decision_tree", "knn"], help="Model pipeline to use")
    parser.add_argument("--elevation", type=float, default=2950, help="Elevation in meters")
    parser.add_argument("--slope", type=float, default=14, help="Slope in degrees")
    parser.add_argument("--aspect", type=float, default=120, help="Aspect in degrees azimuth")
    parser.add_argument("--dist-road", type=float, default=1800, help="Horizontal distance to roadways")
    parser.add_argument("--dist-fire", type=float, default=1950, help="Horizontal distance to fire ignition points")
    parser.add_argument("--wilderness", type=int, default=1, choices=[1, 2, 3, 4], help="Wilderness area (1-4)")
    parser.add_argument("--soil", type=int, default=29, choices=list(range(1, 41)), help="Soil type (1-40)")
    parser.add_argument("--batch-file", type=str, default=None, help="Path to input CSV for batch prediction")
    parser.add_argument("--output-file", type=str, default=None, help="Path to save batch predictions CSV")

    args = parser.parse_args()

    if args.batch_file:
        input_p = Path(args.batch_file)
        if not input_p.exists():
            print(f"Error: Batch file not found: {input_p}", file=sys.stderr)
            return 1

        print(f"Executing batch prediction on {input_p} with {args.model}...")
        df_in = pd.read_csv(input_p)
        df_out = predict_batch(df_in, model_name=args.model)
        out_p = Path(args.output_file) if args.output_file else input_p.with_name(f"{input_p.stem}_predicted.csv")
        df_out.to_csv(out_p, index=False)
        print(f"Wrote {len(df_out)} predictions to {out_p}")
        return 0

    # Single prediction from CLI arguments
    features: Dict[str, float] = {
        "Elevation": args.elevation,
        "Aspect": args.aspect,
        "Slope": args.slope,
        "Horizontal_Distance_To_Hydrology": 250.0,
        "Vertical_Distance_To_Hydrology": 30.0,
        "Horizontal_Distance_To_Roadways": args.dist_road,
        "Hillshade_9am": float(min(255, max(0, int(200 - args.aspect * 0.2)))),
        "Hillshade_Noon": float(min(255, max(0, int(240 - args.slope * 1.5)))),
        "Hillshade_3pm": float(min(255, max(0, int(140 + args.aspect * 0.25)))),
        "Horizontal_Distance_To_Fire_Points": args.dist_fire,
    }
    for i in range(1, 5):
        features[f"Wilderness_Area{i}"] = 1.0 if i == args.wilderness else 0.0
    for i in range(1, 41):
        features[f"Soil_Type{i}"] = 1.0 if i == args.soil else 0.0

    print("=" * 70)
    print(" FOREST COVER TYPE ML PREDICTION PIPELINE")
    print("=" * 70)
    print(f"Input: Elevation={args.elevation}m, Slope={args.slope}°, Wilderness={args.wilderness}, Soil={args.soil}")
    res = predict_single(features, model_name=args.model)
    print(f"Result: Class {res['predicted_cover_type']} -> {res['cover_name']}")
    print(f"Model:  {res['model_used']} (Latency: {res['latency_ms']}ms)")
    if res["probabilities"]:
        print("\nSpecies Probability Distribution:")
        for sp, p in sorted(res["probabilities"].items(), key=lambda x: -x[1]):
            bar = "#" * int(p * 30)
            print(f"  {sp:<24} | {p:>6.2%} | {bar}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
