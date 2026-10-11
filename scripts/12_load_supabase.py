"""Script 12: Initialize Supabase Database & Load Curated Data.

Implements Supabase / PostgreSQL loading:
- Parameterized queries and transactional schema execution
- Multi-schema isolation: raw, curated, analytics, models, app
- Supabase Row Level Security (RLS) setup
- Idempotent data loading (verifies source_manifests before reloading)
- Bulk batch streaming
- Supabase health check and fallback instructions
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from python_src.config import settings
from python_src.database import (
    check_dataset_already_loaded,
    execute_sql_file,
    get_engine,
    health_check,
    is_db_available,
    is_supabase_configured,
    load_dataframe_to_db,
)
from python_src.ingestion import load_raw_covtype
from python_src.logging_config import get_logger, setup_logging
from python_src.schemas import (
    COVER_TYPE_NAMES,
    TARGET_COLUMN,
    WILDERNESS_AREA_NAMES,
    WILDERNESS_FEATURES,
)

setup_logging()
logger = get_logger(__name__)


def compute_file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    settings.ensure_dirs()
    logger.info("=== Practical / Section 12: Supabase Database Loader ===")

    if not is_db_available() and not is_supabase_configured():
        logger.warning(
            "Neither SUPABASE_DB_URL nor DATABASE_URL is configured.\n"
            "To connect your live Supabase database:\n"
            "  1. Go to Supabase Dashboard -> Settings -> Database -> Connection string\n"
            "  2. Copy URI (pooler mode, port 6543) and set in .env:\n"
            "     SUPABASE_DB_URL=postgresql+psycopg://postgres.<proj>:<pass>@aws-0-<region>.pooler.supabase.com:6543/postgres\n"
            "  3. Set SUPABASE_URL and SUPABASE_KEY for REST API client access.\n"
            "Continuing gracefully in STANDALONE_MODE (local exports & files available)."
        )
        return 0

    # 1. Health check
    health = health_check()
    logger.info("Supabase Health Check: %s", health)
    if health.get("status") not in ("OK", "STANDALONE_MODE"):
        logger.error("Database connection failed: %s", health)
        return 1

    if not is_db_available():
        logger.info("Supabase client configured, but SQL engine URL not set. Standalone mode preserved.")
        return 0

    # 2. Execute schema & views
    db_dir = Path(__file__).parent.parent / "database"
    supabase_sql = db_dir / "supabase_migration.sql"
    views_sql = db_dir / "views.sql"

    if supabase_sql.exists():
        logger.info("Executing Supabase migrations: %s", supabase_sql)
        execute_sql_file(supabase_sql)

    if views_sql.exists():
        logger.info("Executing analytical views: %s", views_sql)
        try:
            execute_sql_file(views_sql)
        except Exception as exc:
            logger.warning("Views migration notice: %s", exc)

    # 3. Check if already loaded
    dataset_version = "covtype-1.0-raw"
    if check_dataset_already_loaded(dataset_version, schema="raw", table="source_manifests"):
        logger.info("Dataset version '%s' is already loaded in Supabase. Skipping reload.", dataset_version)
        return 0

    # 4. Load curated data
    logger.info("Loading raw dataset for Supabase ingestion...")
    df = load_raw_covtype(settings.raw_covtype)

    db_df = df.copy()
    wa_cols = [c for c in WILDERNESS_FEATURES if c in db_df.columns]

    def get_wa_name(row):
        for col in wa_cols:
            if row[col] == 1:
                return WILDERNESS_AREA_NAMES.get(col, col)
        return "Unknown"

    db_df["wilderness_area_name"] = db_df.apply(get_wa_name, axis=1)
    db_df["cover_type_name"] = db_df[TARGET_COLUMN].map(
        lambda x: COVER_TYPE_NAMES.get(int(x), f"Class {x}")
    )

    column_mapping = {
        "Elevation": "elevation",
        "Aspect": "aspect",
        "Slope": "slope",
        "Horizontal_Distance_To_Hydrology": "horizontal_distance_to_hydrology",
        "Vertical_Distance_To_Hydrology": "vertical_distance_to_hydrology",
        "Horizontal_Distance_To_Roadways": "horizontal_distance_to_roadways",
        "Hillshade_9am": "hillshade_9am",
        "Hillshade_Noon": "hillshade_noon",
        "Hillshade_3pm": "hillshade_3pm",
        "Horizontal_Distance_To_Fire_Points": "horizontal_distance_to_fire_points",
        "Wilderness_Area1": "wilderness_area_1",
        "Wilderness_Area2": "wilderness_area_2",
        "Wilderness_Area3": "wilderness_area_3",
        "Wilderness_Area4": "wilderness_area_4",
        "Cover_Type": "cover_type",
    }
    db_df = db_df.rename(columns=column_mapping)
    keep_cols = list(column_mapping.values()) + ["wilderness_area_name", "cover_type_name"]
    load_cols = [c for c in keep_cols if c in db_df.columns]

    logger.info("Inserting curated rows into Supabase curated.forest_cover...")
    load_dataframe_to_db(
        db_df[load_cols],
        table_name="forest_cover",
        schema="curated",
        if_exists="append",
        chunk_size=10_000,
    )

    # 5. Record ingestion manifest
    manifest_df = pd.DataFrame([{
        "dataset_name": "Forest CoverType",
        "dataset_version": dataset_version,
        "source_file_path": str(settings.raw_covtype),
        "sha256_hash": compute_file_sha256(settings.raw_covtype),
        "row_count": len(df),
        "column_count": len(df.columns),
        "status": "SUCCESS",
        "notes": "Loaded via scripts/12_load_supabase.py",
    }])
    load_dataframe_to_db(
        manifest_df,
        table_name="source_manifests",
        schema="raw",
        if_exists="append",
    )
    logger.info("Ingestion manifest logged in Supabase raw.source_manifests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
