"""FastAPI Backend Application
Forest Cover Type Prediction & Wildfire-Risk Analysis Analytics System

Integrated Endpoints:
- GET  /health
- GET  /api/supabase/status
- GET  /api/dataset/summary
- GET  /api/dataset/distribution
- GET  /api/dataset/features
- GET  /api/data-quality/report
- GET  /api/cleaning/synthetic-demo
- GET  /api/statistics/descriptive
- GET  /api/features/pca-analysis
- GET  /api/models/metrics
- GET  /api/clusters/summary
- GET  /api/regression/metrics
- POST /api/predict
- GET  /api/wildfire-screening/summary
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to sys.path
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from python_src.config import settings
from python_src.database import health_check as db_health_check, is_db_available, is_supabase_configured
from python_src.logging_config import get_logger, setup_logging
from python_src.pipeline import pipeline_dag
from python_src.schemas import (
    ALL_FEATURES,
    BINARY_FEATURES,
    CONTINUOUS_FEATURES,
    CONTINUOUS_VALID_RANGES,
    COVER_TYPE_NAMES,
    SOIL_FEATURES,
    TARGET_CLASSES,
    WILDERNESS_AREA_NAMES,
    WILDERNESS_FEATURES,
)

setup_logging()
logger = get_logger("backend")

app = FastAPI(
    title="Forest Cover Type & Wildfire-Risk Analytics API",
    description="High-performance analytics, predictions, Supabase integration, and exploratory screening API.",
    version="1.0.0",
)

# CORS configuration (Supports Localhost, Vercel Production, and Vercel Previews)
cors_env = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True if "*" not in origins else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cached models
_CACHED_MODELS: Dict[str, Any] = {}


def get_model(model_name: str = "random_forest"):
    """Load model pipeline from models/ directory with caching."""
    if model_name in _CACHED_MODELS:
        return _CACHED_MODELS[model_name]

    model_file = settings.models_dir / f"{model_name}.joblib"
    if model_file.exists():
        try:
            model = joblib.load(model_file)
            _CACHED_MODELS[model_name] = model
            logger.info("Loaded model '%s' from %s", model_name, model_file)
            return model
        except Exception as exc:
            logger.error("Failed to load model %s: %s", model_file, exc)
    return None


# ---------------------------------------------------------------------------
# Pydantic Request & Response Models
# ---------------------------------------------------------------------------

class PredictionRequest(BaseModel):
    features: Dict[str, float] = Field(
        ...,
        description="Dictionary mapping exactly all 54 feature names to numerical values.",
    )
    model: Optional[str] = Field("random_forest", description="Model to use: 'random_forest', 'decision_tree', 'knn'")


class PredictionResponse(BaseModel):
    predicted_cover_type: int
    cover_name: str
    probabilities: Optional[Dict[str, float]] = None
    model_used: str
    timestamp: str


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
def health():
    """Health check endpoint checking service and Supabase / database status."""
    db_status = db_health_check()
    return {
        "status": "OK",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
        "models_available": [
            f.stem for f in settings.models_dir.glob("*.joblib")
        ] if settings.models_dir.exists() else [],
    }


@app.get("/api/supabase/status", tags=["System"])
def get_supabase_status():
    """Returns detailed Supabase connectivity and configuration status."""
    return {
        "supabase_configured": is_supabase_configured(),
        "database_url_configured": is_db_available(),
        "health": db_health_check(),
        "mode": "CONNECTED" if is_db_available() else "STANDALONE_LOCAL_EXPORTS",
        "supported_schemas": ["raw", "curated", "analytics", "models", "app"],
    }


@app.get("/api/integrations/roundtrip-audit", tags=["Integrations"])
def get_roundtrip_integration_audit():
    """Returns complete bidirectional integration audit for KNIME, Tableau, and Supabase."""
    from python_src.knime_integration import run_full_roundtrip_audit
    return run_full_roundtrip_audit()


@app.get("/api/integrations/knime-status", tags=["Integrations"])
def get_knime_integration_status():
    """Returns input/output verification status and statistical parity delta for KNIME."""
    from python_src.knime_integration import (
        compare_python_and_knime_metrics,
        ingest_and_verify_knime_outputs,
        verify_python_to_knime_inputs,
    )
    return {
        "inputs": verify_python_to_knime_inputs(),
        "outputs": ingest_and_verify_knime_outputs(),
        "statistical_parity": compare_python_and_knime_metrics(),
    }


@app.get("/api/integrations/tableau-status", tags=["Integrations"])
def get_tableau_integration_status():
    """Returns status of Tableau data extracts, workbooks, and calculated fields."""
    from python_src.knime_integration import verify_tableau_integration
    return verify_tableau_integration()


@app.get("/api/dataset/summary", tags=["Dataset"])
def get_dataset_summary():
    """Returns dataset summary metrics and schema definitions."""
    summary_path = settings.statistics_dir / "dataset_summary.json"
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "n_rows" in data and "total_rows" not in data:
                data["total_rows"] = data["n_rows"]
            return data

    return {
        "dataset_name": "Forest CoverType (Roosevelt National Forest)",
        "total_rows": 581012,
        "total_columns": 55,
        "continuous_features_count": len(CONTINUOUS_FEATURES),
        "wilderness_areas_count": len(WILDERNESS_FEATURES),
        "soil_types_count": len(SOIL_FEATURES),
        "classes_count": 7,
    }


@app.get("/api/dataset/distribution", tags=["Dataset"])
def get_dataset_distribution():
    """Returns class distribution counts and percentages."""
    dist_path = settings.knime_exports_dir / "class_distribution.csv"
    if dist_path.exists():
        df = pd.read_csv(dist_path)
        return df.to_dict(orient="records")

    return [
        {"Cover_Type": 1, "cover_name": "Spruce/Fir", "count": 211840, "pct": 36.46},
        {"Cover_Type": 2, "cover_name": "Lodgepole Pine", "count": 283301, "pct": 48.76},
        {"Cover_Type": 3, "cover_name": "Ponderosa Pine", "count": 35754, "pct": 6.15},
        {"Cover_Type": 4, "cover_name": "Cottonwood/Willow", "count": 2747, "pct": 0.47},
        {"Cover_Type": 5, "cover_name": "Aspen", "count": 9493, "pct": 1.63},
        {"Cover_Type": 6, "cover_name": "Douglas-fir", "count": 17367, "pct": 2.99},
        {"Cover_Type": 7, "cover_name": "Krummholz", "count": 20510, "pct": 3.53},
    ]


@app.get("/api/dataset/features", tags=["Dataset"])
def get_dataset_features():
    """Returns descriptions, valid ranges, and types for all 54 input predictors."""
    dict_path = settings.knime_exports_dir / "data_dictionary.csv"
    if dict_path.exists():
        df = pd.read_csv(dict_path)
        return df.to_dict(orient="records")

    features = []
    for col in CONTINUOUS_FEATURES:
        lo, hi = CONTINUOUS_VALID_RANGES.get(col, (0, 0))
        features.append({
            "column": col,
            "type": "Continuous",
            "range": f"[{lo}, {hi}]",
            "description": f"Measurement in meters or degrees ({col}).",
        })
    for col in WILDERNESS_FEATURES:
        features.append({
            "column": col,
            "type": "Binary",
            "range": "{0, 1}",
            "description": f"Wilderness area: {WILDERNESS_AREA_NAMES.get(col, col)}.",
        })
    for col in SOIL_FEATURES:
        features.append({
            "column": col,
            "type": "Binary",
            "range": "{0, 1}",
            "description": f"Soil type indicator: {col}.",
        })
    return features


@app.get("/api/data-quality/report", tags=["Quality"])
def get_data_quality_report():
    """Returns data quality audit and synthetic missing-value experiment results."""
    res: Dict[str, Any] = {}
    q_path = settings.reports_dir / "data_quality" / "audit_report.md"
    if q_path.exists():
        with open(q_path, "r", encoding="utf-8") as f:
            res["audit_markdown"] = f.read()

    demo_report = settings.reports_dir / "data_quality" / "synthetic_demo_audit.json"
    if demo_report.exists():
        with open(demo_report, "r", encoding="utf-8") as f:
            res["synthetic_cleaning_experiment"] = json.load(f)

    outlier_path = settings.reports_dir / "data_quality" / "outlier_comparison.csv"
    if outlier_path.exists():
        res["outliers"] = pd.read_csv(outlier_path).to_dict(orient="records")

    return res


@app.get("/api/cleaning/synthetic-demo", tags=["Quality"])
def get_synthetic_demo_details():
    """Returns dedicated results of Practical 2: 800-cell synthetic missing values experiment."""
    demo_report = settings.reports_dir / "data_quality" / "synthetic_demo_audit.json"
    if demo_report.exists():
        with open(demo_report, "r", encoding="utf-8") as f:
            return json.load(f)

    return {
        "status": "NOT_FOUND",
        "message": "Run scripts/03_synthetic_cleaning_demo.py to generate demonstration records."
    }


@app.get("/api/statistics/descriptive", tags=["Statistics"])
def get_descriptive_statistics():
    """Returns 5-number summary, mean, std, skewness, and kurtosis for continuous predictors."""
    stats_csv = settings.statistics_dir / "descriptive_statistics.csv"
    if stats_csv.exists():
        df = pd.read_csv(stats_csv)
        return df.to_dict(orient="records")

    return {"status": "NO_STATISTICS_YET", "message": "Run scripts/05_descriptive_statistics.py"}


@app.get("/api/features/pca-analysis", tags=["Feature Engineering"])
def get_pca_analysis():
    """Returns Principal Component Analysis (PCA) report and feature loadings."""
    pca_json = settings.statistics_dir / "pca_report.json"
    pca_loadings_csv = settings.statistics_dir / "pca_loadings.csv"

    res: Dict[str, Any] = {}
    if pca_json.exists():
        with open(pca_json, "r", encoding="utf-8") as f:
            res["summary"] = json.load(f)
    if pca_loadings_csv.exists():
        res["loadings"] = pd.read_csv(pca_loadings_csv).to_dict(orient="records")

    ranking_csv = settings.statistics_dir / "feature_ranking_combined.csv"
    if ranking_csv.exists():
        res["feature_rankings"] = pd.read_csv(ranking_csv).to_dict(orient="records")

    return res if res else {"status": "NO_PCA_YET", "message": "Run scripts/07_feature_selection_pca.py"}


@app.get("/api/models/metrics", tags=["Models"])
def get_model_metrics():
    """Returns classification model evaluation metrics and comparison summary."""
    metrics_path = settings.statistics_dir / "classification_metrics.json"
    if metrics_path.exists():
        with open(metrics_path, "r", encoding="utf-8") as f:
            return json.load(f)

    summary_csv = settings.statistics_dir / "classification_metrics_summary.csv"
    if summary_csv.exists():
        return {"metrics": pd.read_csv(summary_csv).to_dict(orient="records")}

    return {"status": "NO_METRICS_YET", "message": "Run scripts/08_train_classifiers.py"}


@app.get("/api/clusters/summary", tags=["Clustering"])
def get_clusters_summary():
    """Returns K-Means cluster profiles and elbow/silhouette analysis."""
    profiles_csv = settings.statistics_dir / "cluster_profiles.csv"
    elbow_csv = settings.statistics_dir / "cluster_elbow_silhouette.csv"

    res: Dict[str, Any] = {}
    if profiles_csv.exists():
        res["profiles"] = pd.read_csv(profiles_csv).to_dict(orient="records")
    if elbow_csv.exists():
        res["evaluation"] = pd.read_csv(elbow_csv).to_dict(orient="records")

    return res if res else {"status": "NO_CLUSTERS_YET", "message": "Run scripts/09_run_clustering.py"}


@app.get("/api/regression/metrics", tags=["Regression"])
def get_regression_metrics():
    """Returns UCI Forest Fires regression benchmark results (Practical 9)."""
    fires_json = settings.statistics_dir / "forest_fires_regression_summary.json"
    if fires_json.exists():
        with open(fires_json, "r", encoding="utf-8") as f:
            return json.load(f)

    return {"status": "NO_REGRESSION_YET", "message": "Run scripts/10_train_fires_regression.py"}


@app.post("/api/predict", response_model=PredictionResponse, tags=["Inference"])
def predict_cover_type(req: PredictionRequest):
    """Predicts forest cover type given all 54 environmental features.

    Validates schema, ensures strict column ordering matching training data,
    and returns prediction + class probabilities.
    """
    model_name = req.model.lower().replace(" ", "_") if req.model else "random_forest"
    model = get_model(model_name)
    if model is None:
        for candidate in ["random_forest", "decision_tree", "knn"]:
            model = get_model(candidate)
            if model is not None:
                model_name = candidate
                break

    # Build feature vector in exact schema order
    input_values = []
    missing_cols = []
    for col in ALL_FEATURES:
        if col in req.features:
            input_values.append(float(req.features[col]))
        else:
            missing_cols.append(col)

    if missing_cols:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required features ({len(missing_cols)}): {missing_cols[:5]}...",
        )

    X_in = np.array([input_values])

    if model is not None:
        pred_class = int(model.predict(X_in)[0])
        probabilities = None
        if hasattr(model, "predict_proba"):
            try:
                probs = model.predict_proba(X_in)[0]
                classes = model.classes_
                probabilities = {
                    COVER_TYPE_NAMES.get(int(c), str(c)): round(float(p), 4)
                    for c, p in zip(classes, probs)
                }
            except Exception:
                pass
    else:
        # Ecological heuristic fallback if model weights not yet trained
        elev = req.features.get("Elevation", 2500)
        if elev > 3100:
            pred_class = 7 if elev > 3300 else 1
        elif elev > 2800:
            pred_class = 2
        elif elev < 2200:
            pred_class = 4
        elif elev < 2500:
            pred_class = 3
        else:
            pred_class = 2
        probabilities = {
            COVER_TYPE_NAMES[c]: 0.85 if c == pred_class else round(0.15 / 6, 3)
            for c in TARGET_CLASSES
        }
        model_name = "ecological_heuristic_fallback"

    return PredictionResponse(
        predicted_cover_type=pred_class,
        cover_name=COVER_TYPE_NAMES.get(pred_class, f"Class {pred_class}"),
        probabilities=probabilities,
        model_used=model_name,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/wildfire-screening/summary", tags=["Wildfire Screening"])
def get_wildfire_screening_summary():
    """Returns topographic wildfire risk screening aggregates with explicit limitations.

    IMPORTANT DISCLAIMER: This is an exploratory terrain screening score,
    NOT a calibrated probability of wildfire occurrence.
    """
    agg_csv = settings.tableau_exports_dir / "wildfire_screening_aggregates.csv"
    data = []
    if agg_csv.exists():
        df_agg = pd.read_csv(agg_csv).dropna(subset=["mean_screening_risk_score"])
        df_agg = df_agg.fillna(0)
        data = df_agg.to_dict(orient="records")

    return {
        "methodology": {
            "description": "Exploratory topographic screening score derived from proximity to historical ignition points, slope steepness, and solar radiation index.",
            "formula": "Score = (0.40 * Proximity + 0.35 * SlopeFactor + 0.25 * SolarExposure) * 100",
            "limitations": [
                "Does NOT represent empirical ignition probability or future fire recurrence forecast.",
                "Weather conditions (wind, relative humidity, fuel moisture) are not present in Covertype.",
                "Used strictly for comparative terrain hazard screening."
            ],
        },
        "aggregates": data,
    }


@app.get("/api/pipeline/status", tags=["Pipeline Orchestrator"])
def get_pipeline_status():
    """Returns current pipeline artifact verification status and latest execution manifest."""
    validation = pipeline_dag.validate_existing_artifacts()

    manifest_file = settings.reports_dir / "pipeline_run_manifest.json"
    manifest = None
    if manifest_file.exists():
        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as exc:
            logger.warning("Could not read pipeline manifest: %s", exc)

    return {
        "status": "VALIDATED" if validation["all_stages_validated"] else "DEGRADED",
        "validated_count": validation["validated_count"],
        "total_stages": validation["total_stages"],
        "checked_at": validation["checked_at"],
        "stages": validation["stages"],
        "latest_run_manifest": manifest,
    }


@app.get("/api/pipeline/stages", tags=["Pipeline Orchestrator"])
def get_pipeline_stages():
    """Returns full directed acyclic graph (DAG) topology, stage metadata, inputs, and outputs."""
    return pipeline_dag.get_dag_topology()


@app.post("/api/pipeline/validate", tags=["Pipeline Orchestrator"])
def trigger_pipeline_validation():
    """Re-audits all 12 pipeline stage artifacts and returns updated checkpoint results."""
    res = pipeline_dag.validate_existing_artifacts()
    return {
        "status": "VALIDATED" if res["all_stages_validated"] else "DEGRADED",
        "validated_count": res["validated_count"],
        "total_stages": res["total_stages"],
        "checked_at": res["checked_at"],
        "stages": res["stages"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
