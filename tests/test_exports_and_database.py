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
