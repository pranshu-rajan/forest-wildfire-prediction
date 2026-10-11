"""
Configuration loader for the forest-cover pipeline.

Reads ``config.yaml`` from the project root and exposes a single
``Settings`` dataclass.  Override any value with an environment variable
of the form ``FCWF_<KEY>`` (e.g. ``FCWF_RANDOM_SEED=0``).

Environment variables for secrets (DATABASE_URL, etc.) are loaded from
``.env`` if ``python-dotenv`` is installed, otherwise from the process
environment directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

# ---------------------------------------------------------------------------
# Resolve project root regardless of where the script is invoked from
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent          # python_src/
PROJECT_ROOT = _HERE.parent            # forest-cover-wildfire/
CONFIG_FILE = PROJECT_ROOT / "config.yaml"


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _env(key: str, default: str | None = None) -> str | None:
    """Read from FCWF_ prefixed env var, then plain key, then default."""
    return os.environ.get(f"FCWF_{key.upper()}", os.environ.get(key.upper(), default))


@dataclass
class Settings:
    # --- project metadata ---
    project_name: str = "forest-cover-wildfire"
    dataset_version: str = "covtype-v1"
    feature_schema_version: str = "covtype-features-v1"
    random_seed: int = 42
    test_size: float = 0.20

    # --- paths (resolved to absolute) ---
    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data")
    external_data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data/external")
    raw_covtype: Path = field(default_factory=lambda: PROJECT_ROOT / "data/raw/covtype.csv")
    processed_covtype: Path = field(default_factory=lambda: PROJECT_ROOT / "data/processed/covtype_clean.parquet")
    reports_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "reports")
    figures_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "reports/figures")
    statistics_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "reports/statistics")
    data_quality_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "reports/data_quality")
    practical_evidence_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "reports/practical_evidence")
    models_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "models")
    exports_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "exports")
    knime_exports_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "exports/knime")
    knime_outputs_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "exports/knime_outputs")
    tableau_exports_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "exports/tableau")
    external_data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data/external")
    synthetic_data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data/synthetic")
    processed_data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data/processed")

    # --- cleaning / demo ---
    iqr_multiplier: float = 1.5
    zscore_threshold: float = 3.0
    synthetic_missing_demo_rows: int = 10_000
    synthetic_missing_fraction: float = 0.02   # 800 / (10000 * 10 cont cols) ≈ 0.008; kept for ref

    # --- database ---
    database_url: Optional[str] = None

    # --- derived ---
    @property
    def demo_raw_path(self) -> Path:
        return self.processed_data_dir / "covtype_missing_values_demo.csv"

    @property
    def demo_clean_path(self) -> Path:
        return self.processed_data_dir / "covtype_missing_values_demo_clean.csv"

    def ensure_dirs(self) -> None:
        """Create all output directories if they do not exist."""
        dirs = [
            self.reports_dir, self.figures_dir, self.statistics_dir,
            self.data_quality_dir, self.practical_evidence_dir,
            self.models_dir, self.exports_dir, self.knime_exports_dir,
            self.tableau_exports_dir, self.external_data_dir,
            self.synthetic_data_dir, self.processed_data_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)


def load_settings(config_path: Path | None = None) -> Settings:
    """Load settings from YAML, then apply env-variable overrides."""
    path = config_path or CONFIG_FILE
    raw: dict = {}
    if path.exists():
        raw = _load_yaml(path)

    proj = raw.get("project", {})
    paths = raw.get("paths", {})
    cleaning = raw.get("cleaning", {})

    def _resolve(p: str) -> Path:
        """Make a path absolute relative to project root."""
        return (PROJECT_ROOT / p).resolve()

    s = Settings(
        project_name=proj.get("name", "forest-cover-wildfire"),
        dataset_version=proj.get("dataset_version", "covtype-v1"),
        feature_schema_version=proj.get("feature_schema_version", "covtype-features-v1"),
        random_seed=int(_env("RANDOM_SEED") or proj.get("random_seed", 42)),
        test_size=float(_env("TEST_SIZE") or proj.get("test_size", 0.20)),
        raw_covtype=_resolve(paths.get("raw_covtype", "data/raw/covtype.csv")),
        processed_covtype=_resolve(paths.get("processed_covtype", "data/processed/covtype_clean.parquet")),
        reports_dir=_resolve(paths.get("reports_dir", "reports")),
        figures_dir=_resolve(paths.get("reports_dir", "reports")) / "figures",
        statistics_dir=_resolve(paths.get("reports_dir", "reports")) / "statistics",
        data_quality_dir=_resolve(paths.get("reports_dir", "reports")) / "data_quality",
        practical_evidence_dir=_resolve(paths.get("reports_dir", "reports")) / "practical_evidence",
        models_dir=_resolve("models"),
        exports_dir=_resolve("exports"),
        knime_exports_dir=_resolve("exports/knime"),
        tableau_exports_dir=_resolve("exports/tableau"),
        external_data_dir=_resolve("data/external"),
        synthetic_data_dir=_resolve("data/synthetic"),
        processed_data_dir=_resolve("data/processed"),
        iqr_multiplier=float(cleaning.get("iqr_multiplier", 1.5)),
        zscore_threshold=float(cleaning.get("zscore_threshold", 3.0)),
        synthetic_missing_demo_rows=int(cleaning.get("synthetic_missing_demo_rows", 10_000)),
        database_url=_env("DATABASE_URL"),
    )
    return s


# Module-level singleton — import and use directly
settings: Settings = load_settings()
