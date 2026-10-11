"""
Unit tests for FastAPI endpoints: health, datasets, quality, predictions, clusters, screening.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from python_src.schemas import ALL_FEATURES

client = TestClient(app)


def test_health_endpoint():
    """Verify health endpoint returns status OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OK"
    assert "timestamp" in data


def test_dataset_summary_and_distribution():
    """Verify dataset summary and distribution endpoints return structured data."""
    res_summary = client.get("/api/dataset/summary")
    assert res_summary.status_code == 200
    assert "total_rows" in res_summary.json()

    res_dist = client.get("/api/dataset/distribution")
    assert res_dist.status_code == 200
    assert len(res_dist.json()) == 7


def test_dataset_features():
    """Verify feature dictionary endpoint lists all 54 predictors."""
    response = client.get("/api/dataset/features")
    assert response.status_code == 200
    features = response.json()
    assert len(features) in (len(ALL_FEATURES), len(ALL_FEATURES) + 1)


def test_predict_endpoint_valid_features(sample_feature_dict):
    """Verify predict endpoint succeeds with full valid 54-feature payload."""
    payload = {
        "features": sample_feature_dict,
        "model": "random_forest",
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_cover_type" in data
    assert 1 <= data["predicted_cover_type"] <= 7
    assert "cover_name" in data


def test_predict_endpoint_missing_features():
    """Verify predict endpoint rejects incomplete feature sets with 422 Unprocessable Entity."""
    payload = {
        "features": {"Elevation": 2500, "Slope": 15},  # Incomplete: missing other 52 features
        "model": "random_forest",
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 422


def test_wildfire_screening_endpoint():
    """Verify wildfire screening endpoint includes explicit limitations and formulas."""
    response = client.get("/api/wildfire-screening/summary")
    assert response.status_code == 200
    data = response.json()
    assert "methodology" in data
    assert "limitations" in data["methodology"]


def test_supabase_and_new_endpoints():
    """Verify Supabase status, descriptive statistics, PCA, regression, and synthetic demo endpoints."""
    res_sb = client.get("/api/supabase/status")
    assert res_sb.status_code == 200
    assert "supported_schemas" in res_sb.json()

    res_stats = client.get("/api/statistics/descriptive")
    assert res_stats.status_code == 200

    res_pca = client.get("/api/features/pca-analysis")
    assert res_pca.status_code == 200

    res_reg = client.get("/api/regression/metrics")
    assert res_reg.status_code == 200

    res_demo = client.get("/api/cleaning/synthetic-demo")
    assert res_demo.status_code == 200


def test_pipeline_status_and_stages_endpoints():
    """Verify Pipeline orchestrator endpoints return DAG status and topology."""
    res_status = client.get("/api/pipeline/status")
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert "status" in data_status
    assert data_status["total_stages"] == 12
    assert "stages" in data_status

    res_stages = client.get("/api/pipeline/stages")
    assert res_stages.status_code == 200
    data_stages = res_stages.json()
    assert data_stages["total_nodes"] == 12
    assert len(data_stages["edges"]) > 0
    assert "nodes" in data_stages

