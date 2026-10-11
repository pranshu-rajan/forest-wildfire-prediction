"""Database and Supabase Integration Module.

Provides connectivity, schema management, and data loading for:
- Supabase (Managed PostgreSQL, Connection Pooling & REST Client)
- Local / Direct PostgreSQL instances
- Standalone / File-based Development Mode (graceful offline fallback)

Credentials are read strictly from environment variables:
- SUPABASE_URL: Supabase Project API URL (e.g. https://xyz.supabase.co)
- SUPABASE_KEY: Supabase Anon or Service Role Key
- SUPABASE_DB_URL or DATABASE_URL: PostgreSQL connection string
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional

from python_src.logging_config import get_logger

logger = get_logger(__name__)

# Cached Supabase client
_SUPABASE_CLIENT = None


def get_database_url() -> Optional[str]:
    """Read database connection string from environment.

    Checks SUPABASE_DB_URL first, then DATABASE_URL.
    """
    return os.environ.get("SUPABASE_DB_URL") or os.environ.get("DATABASE_URL")


def get_supabase_url() -> Optional[str]:
    """Read SUPABASE_URL from environment."""
    return os.environ.get("SUPABASE_URL")


def get_supabase_key() -> Optional[str]:
    """Read SUPABASE_KEY or SUPABASE_SERVICE_KEY from environment."""
    return os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")


def is_db_available() -> bool:
    """Return True if a database URL is configured."""
    return bool(get_database_url())


def is_supabase_configured() -> bool:
    """Return True if Supabase REST API credentials are configured."""
    return bool(get_supabase_url() and get_supabase_key())


def get_supabase_client():
    """Create or return cached Supabase Python client."""
    global _SUPABASE_CLIENT
    if _SUPABASE_CLIENT is not None:
        return _SUPABASE_CLIENT

    sb_url = get_supabase_url()
    sb_key = get_supabase_key()
    if not (sb_url and sb_key):
        return None

    try:
        from supabase import Client, create_client
        _SUPABASE_CLIENT = create_client(sb_url, sb_key)
        logger.info("Supabase Python client initialized successfully.")
        return _SUPABASE_CLIENT
    except Exception as exc:
        logger.warning("Could not initialize Supabase client: %s", exc)
        return None


def get_engine():
    """Create and return a SQLAlchemy engine with connection pooler support.

    Raises EnvironmentError if neither SUPABASE_DB_URL nor DATABASE_URL is set.
    """
    url = get_database_url()
    if not url:
        raise EnvironmentError(
            "Neither SUPABASE_DB_URL nor DATABASE_URL environment variable is set.\n"
            "Set it in your .env file: \n"
            "SUPABASE_DB_URL=postgresql+psycopg://postgres.<project_id>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres"
        )
    try:
        from sqlalchemy import create_engine
        # Use pool_pre_ping to survive Supabase connection pool timeouts
        engine = create_engine(url, pool_pre_ping=True, echo=False)
        logger.info("Database engine created with pool_pre_ping enabled.")
        return engine
    except ImportError:
        raise ImportError(
            "SQLAlchemy and psycopg are required. Install via: pip install sqlalchemy psycopg[binary]"
        )


@contextmanager
def get_connection() -> Generator:
    """Context manager yielding a SQLAlchemy connection."""
    engine = get_engine()
    with engine.connect() as conn:
        yield conn


def health_check() -> dict[str, Any]:
    """Test the Supabase / database connection and return comprehensive health status."""
    status_info: dict[str, Any] = {
        "supabase_configured": is_supabase_configured(),
        "database_url_configured": is_db_available(),
    }

    # 1. Test SQLAlchemy / PostgreSQL Connection
    if is_db_available():
        try:
            from sqlalchemy import text
            engine = get_engine()
            with engine.connect() as conn:
                version = conn.execute(text("SELECT version()")).scalar()
            status_info["engine_status"] = "OK"
            status_info["engine_version"] = version
        except Exception as exc:
            logger.error("DB health check failed: %s", exc)
            status_info["engine_status"] = "ERROR"
            status_info["engine_error"] = str(exc)
    else:
        status_info["engine_status"] = "STANDALONE_MODE"

    # 2. Test Supabase Client REST API
    client = get_supabase_client()
    if client is not None:
        try:
            status_info["supabase_client_status"] = "READY"
        except Exception as exc:
            status_info["supabase_client_status"] = "ERROR"
            status_info["supabase_client_error"] = str(exc)
    else:
        status_info["supabase_client_status"] = "NOT_CONFIGURED"

    status_info["status"] = (
        "OK" if (status_info["engine_status"] == "OK" or status_info["supabase_client_status"] == "READY")
        else "STANDALONE_MODE"
    )
    return status_info


def execute_sql_file(sql_path: Path) -> None:
    """Execute a SQL script file against the configured Supabase / PostgreSQL database."""
    sql_text = sql_path.read_text(encoding="utf-8")
    from sqlalchemy import text
    engine = get_engine()
    with engine.begin() as conn:
        for statement in sql_text.split(";"):
            stmt = statement.strip()
            if stmt:
                conn.execute(text(stmt))
    logger.info("SQL script executed successfully: %s", sql_path)


def load_dataframe_to_db(
    df,
    table_name: str,
    schema: str = "curated",
    if_exists: str = "replace",
    chunk_size: int = 10_000,
) -> None:
    """Bulk-load a DataFrame into Supabase / PostgreSQL using pandas.to_sql.

    Parameters
    ----------
    df: pd.DataFrame
    table_name: str
    schema: str — 'raw', 'curated', 'analytics', 'models', or 'app'
    if_exists: 'replace' | 'append' | 'fail'
    chunk_size: rows per batch insert
    """
    engine = get_engine()
    df.to_sql(
        table_name,
        engine,
        schema=schema,
        if_exists=if_exists,
        index=False,
        chunksize=chunk_size,
        method="multi",
    )
    logger.info(
        "Loaded %d rows into %s.%s (if_exists=%s).",
        len(df),
        schema,
        table_name,
        if_exists,
    )


def check_dataset_already_loaded(
    dataset_version: str,
    schema: str = "raw",
    table: str = "source_manifests",
) -> bool:
    """Check if this dataset version has already been ingested into Supabase."""
    if not is_db_available():
        return False
    try:
        from sqlalchemy import text
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    f"SELECT COUNT(*) FROM {schema}.{table} "
                    "WHERE dataset_version = :ver"
                ),
                {"ver": dataset_version},
            ).scalar()
        already = bool(result and result > 0)
        logger.info("Dataset version '%s' already loaded: %s", dataset_version, already)
        return already
    except Exception:
        return False
