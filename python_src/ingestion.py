"""
Data ingestion module: load, fingerprint, and attach traceability IDs.

Responsibilities
----------------
- Load the raw Covertype CSV with the correct dtypes.
- Compute a SHA-256 digest of the source file.
- Attach a zero-based ``record_id`` column for row-level traceability.
- Never modify the original source file.
- Log all actions with the module logger.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import pandas as pd

from python_src.logging_config import get_logger
from python_src.schemas import ALL_FEATURES, RAW_CSV_COLUMNS, TARGET_COLUMN, RECORD_ID_COLUMN

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_sha256(path: Path) -> str:
    """Return the hex-encoded SHA-256 digest of *path* without loading into RAM."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_raw_covtype(path: Path, add_record_id: bool = True) -> pd.DataFrame:
    """Load the raw Covertype CSV and optionally prepend a ``record_id`` column.

    Parameters
    ----------
    path:
        Absolute or relative path to ``covtype.csv``.
    add_record_id:
        When *True* (default), insert a 0-based integer column as the first
        column.  This column is never used as a model feature.

    Returns
    -------
    pd.DataFrame with dtype ``int64`` for all columns.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at '{path}'.\n"
            f"Place the Covertype CSV at data/raw/covtype.csv and retry."
        )

    logger.info("Loading raw dataset from %s …", path)
    t0 = time.perf_counter()

    # Specify dtypes to avoid mixed-type inference on large file
    dtype_map = {col: "int64" for col in RAW_CSV_COLUMNS}
    df = pd.read_csv(path, dtype=dtype_map)

    elapsed = time.perf_counter() - t0
    logger.info("Loaded %d rows × %d columns in %.2f s.", len(df), df.shape[1], elapsed)

    if add_record_id:
        df.insert(0, RECORD_ID_COLUMN, range(len(df)))

    return df


def build_source_manifest(path: Path, df: pd.DataFrame, dataset_version: str) -> dict[str, Any]:
    """Compute a source manifest dict including file metadata and SHA-256."""
    stat = path.stat()
    digest = compute_sha256(path)

    manifest: dict[str, Any] = {
        "dataset_version": dataset_version,
        "source_path": str(path),
        "sha256": digest,
        "file_size_bytes": stat.st_size,
        "row_count": int(len(df)),
        "column_count": int(df.shape[1]),
        "columns": list(df.columns),
        "ingested_at": pd.Timestamp.now(tz="UTC").isoformat(),
    }
    return manifest


def save_manifest(manifest: dict[str, Any], out_path: Path) -> None:
    """Serialise *manifest* to JSON at *out_path*."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    logger.info("Manifest saved to %s", out_path)


def load_parquet(path: Path) -> pd.DataFrame:
    """Load a processed Parquet file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Processed dataset not found at '{path}'.\n"
            "Run 'python scripts/01_audit_source.py' first."
        )
    logger.info("Loading Parquet dataset from %s …", path)
    return pd.read_parquet(path)
