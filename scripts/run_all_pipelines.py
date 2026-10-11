"""
Unified orchestration script: runs all pipeline stages sequentially.

Usage:
    python scripts/run_all_pipelines.py [--skip-slow]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    ("01_audit_source.py", "Phase 1: Source dataset audit"),
    ("02_run_cleaning.py", "Phase 1: Real-data cleaning pipeline"),
    ("03_synthetic_cleaning_demo.py", "Phase 1: Synthetic missing-value cleaning demo"),
    ("04_generate_eda.py", "Phase 2: Exploratory data analysis & visualizations"),
    ("05_descriptive_statistics.py", "Phase 2: Descriptive statistics table & formulas"),
    ("06_preprocessing_experiments.py", "Phase 3: Preprocessing experiments (scaling/binning)"),
    ("07_feature_selection_pca.py", "Phase 4: Feature selection & PCA decomposition"),
    ("08_train_classifiers.py", "Phase 5: Classification models (DT, RF, KNN)"),
    ("09_run_clustering.py", "Phase 6: Clustering analysis (K-Means, Agglomerative)"),
    ("10_train_fires_regression.py", "Phase 6: Forest Fires regression analysis"),
    ("11_export_integrations.py", "Phase 7: KNIME & Tableau integration exports"),
    ("12_load_postgres.py", "Phase 7: PostgreSQL initialization & loading"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run complete analytics pipeline.")
    parser.add_argument("--skip-slow", action="store_true", help="Skip heavy model training stages")
    args = parser.parse_args()

    scripts_dir = Path(__file__).parent
    root_dir = scripts_dir.parent

    print("====================================================================")
    print(" Forest Cover Type Prediction & Wildfire-Risk Analytics Pipeline    ")
    print("====================================================================")

    for script_name, description in SCRIPTS:
        if args.skip_slow and script_name in ["08_train_classifiers.py", "09_run_clustering.py"]:
            print(f"\n[SKIPPED] {script_name} ({description})")
            continue

        print(f"\n--> Running {script_name}: {description}")
        script_path = scripts_dir / script_name
        cmd = [sys.executable, str(script_path)]
        res = subprocess.run(cmd, cwd=root_dir)
        if res.returncode != 0:
            print(f"Error: {script_name} failed with exit code {res.returncode}")
            return res.returncode

    print("\n====================================================================")
    print(" All pipeline stages completed successfully!                        ")
    print("====================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
