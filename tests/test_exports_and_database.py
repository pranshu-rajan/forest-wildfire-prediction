"""
Unit tests for KNIME, Tableau exports, and database integration checks.
"""

from __future__ import annotations

import pandas as pd
import pytest

from python_src.database import health_check, is_db_available
from python_src.exports import (
    export_class_distribution,
    export_covertype_curated,
    export_data_dictionary,
    export_terrain_summary_by_cover,
    export_wildfire_screening_aggregates,
)


def test_export_data_dictionary(tmp_path):
    """Verify data dictionary generation has all columns and valid ranges."""
    path = export_data_dictionary(tmp_path)
    assert path.exists()
    df = pd.read_csv(path)
    assert len(df) == 55  # 54 predictors + 1 target
    assert "column" in df.columns
    assert "valid_range" in df.columns


def test_export_covertype_curated(synthetic_covtype_df: pd.DataFrame, tmp_path):
    """Verify curated flat-file export for KNIME consumption."""
    path = export_covertype_curated(synthetic_covtype_df, tmp_path, sample_n=50)
    assert path.exists()
    df = pd.read_csv(path)
    assert len(df) == 50
    assert "Cover_Type" in df.columns


def test_export_tableau_terrain_and_screening(synthetic_covtype_df: pd.DataFrame, tmp_path):
    """Verify Tableau terrain summary and wildfire screening aggregate exports."""
    terrain_path = export_terrain_summary_by_cover(synthetic_covtype_df, tmp_path)
    assert terrain_path.exists()

    screening_path = export_wildfire_screening_aggregates(synthetic_covtype_df, tmp_path)
    assert screening_path.exists()
    df_scr = pd.read_csv(screening_path)
    assert "mean_screening_risk_score" in df_scr.columns
    assert "risk_tier" in df_scr.columns


def test_database_health_check_without_db():
    """Verify database health check returns safe status when DATABASE_URL is not set."""
    status = health_check()
    assert isinstance(status, dict)
    assert "status" in status


def test_roundtrip_knime_and_tableau_integration():
    """Verify bidirectional round-trip data flow between Python, KNIME, and Tableau."""
    from python_src.knime_integration import (
        compare_python_and_knime_metrics,
        ingest_and_verify_knime_outputs,
        verify_python_to_knime_inputs,
        verify_tableau_integration,
    )

    # 1. Check Python -> KNIME inputs
    inputs_res = verify_python_to_knime_inputs()
    assert inputs_res["all_passed"] is True
    assert inputs_res["files_checked"] >= 7

    # 2. Check KNIME -> Python outputs
    outputs_res = ingest_and_verify_knime_outputs()
    assert outputs_res["all_passed"] is True
    assert outputs_res["files_checked"] >= 5

    # 3. Check statistical parity
    parity_res = compare_python_and_knime_metrics()
    assert parity_res["status"] == "VERIFIED"
    for comp in parity_res["comparisons"]:
        assert comp["absolute_delta"] <= comp["tolerance_threshold"]

    # 4. Check Tableau integration
    tableau_res = verify_tableau_integration()
    assert tableau_res["status"] == "VERIFIED"
    assert len(tableau_res["workbooks"]) == 3
