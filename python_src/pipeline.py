"""Unified Pipeline Orchestration Engine & DAG Manager.

Provides a structured, fault-tolerant, staged pipeline execution framework:
- Formal Stage Abstraction (Name, Practical ID, Syllabus Unit, Pre/Post Assertions)
- Dependency-Preserving DAG Execution Order
- Artifact Verification Checkpoints at every stage boundary
- Telemetry, Timing, and Manifest Logging (reports/pipeline_run_manifest.json)
- Integration with FastAPI (/api/pipeline/status) and Next.js UI
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from python_src.config import PROJECT_ROOT, settings
from python_src.logging_config import get_logger

logger = get_logger("pipeline_orchestrator")


@dataclass
class StageCheckpoint:
    artifact_path: str
    min_size_bytes: int = 10
    required: bool = True

    def verify(self) -> bool:
        p = Path(self.artifact_path)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        return p.exists() and p.stat().st_size >= self.min_size_bytes


@dataclass
class PipelineStage:
    stage_id: str
    name: str
    practical_id: str
    syllabus_unit: str
    script_file: str
    description: str
    depends_on: List[str] = field(default_factory=list)
    inputs: List[StageCheckpoint] = field(default_factory=list)
    outputs: List[StageCheckpoint] = field(default_factory=list)
    status: str = "PENDING"
    duration_sec: float = 0.0
    error_message: Optional[str] = None
    executed_at: Optional[str] = None

    def run(self, fast_mode: bool = False) -> bool:
        """Run stage script, enforce pre/post checkpoints, and record metrics."""
        self.executed_at = datetime.now(timezone.utc).isoformat()
        t0 = time.perf_counter()

        # 1. Pre-condition Assertions
        for inp in self.inputs:
            if inp.required and not inp.verify():
                self.status = "PRE_CHECK_FAILED"
                self.error_message = f"Missing required input checkpoint: {inp.artifact_path}"
                self.duration_sec = time.perf_counter() - t0
                logger.error("[Stage %s] %s", self.stage_id, self.error_message)
                return False

        # 2. Execution
        script_path = PROJECT_ROOT / "scripts" / self.script_file
        if not script_path.exists():
            self.status = "SCRIPT_NOT_FOUND"
            self.error_message = f"Target script does not exist: {script_path}"
            self.duration_sec = time.perf_counter() - t0
            logger.error("[Stage %s] %s", self.stage_id, self.error_message)
            return False

        try:
            logger.info("Executing Stage [%s]: %s (%s)...", self.stage_id, self.name, self.script_file)
            cmd = [sys.executable, str(script_path)]
            result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

            if result.returncode != 0:
                self.status = "FAILED"
                self.error_message = f"Process exited with code {result.returncode}: {result.stderr[:300]}"
                self.duration_sec = time.perf_counter() - t0
                logger.error("[Stage %s] Failure: %s", self.stage_id, self.error_message)
                return False

        except Exception as exc:
            self.status = "EXCEPTION"
            self.error_message = str(exc)
            self.duration_sec = time.perf_counter() - t0
            logger.exception("[Stage %s] Exception occurred", self.stage_id)
            return False

        # 3. Post-condition Checkpoints
        for out in self.outputs:
            if out.required and not out.verify():
                self.status = "POST_CHECK_FAILED"
                self.error_message = f"Output artifact checkpoint failed: {out.artifact_path}"
                self.duration_sec = time.perf_counter() - t0
                logger.error("[Stage %s] %s", self.stage_id, self.error_message)
                return False

        self.duration_sec = round(time.perf_counter() - t0, 3)
        self.status = "SUCCESS"
        self.error_message = None
        logger.info("Stage [%s] completed successfully in %.3fs.", self.stage_id, self.duration_sec)
        return True


class PipelineDAG:
    """Manages the full multi-stage analytics pipeline DAG."""

    def __init__(self):
        self.stages: List[PipelineStage] = [
            PipelineStage(
                stage_id="01_SOURCE_AUDIT",
                name="Source Dataset Cryptographic Audit & Fingerprinting",
                practical_id="Practical 1",
                syllabus_unit="Unit I",
                script_file="01_audit_source.py",
                description="Verifies untouched raw covtype.csv SHA-256 fingerprint, 581,012 rows, 0 nulls.",
                depends_on=[],
                inputs=[StageCheckpoint("data/raw/covtype.csv", min_size_bytes=1000000)],
                outputs=[StageCheckpoint("reports/data_quality/source_manifest.json")],
            ),
            PipelineStage(
                stage_id="02_DATA_CLEANING",
                name="Curated Cleaning & Outlier Detection",
                practical_id="Practical 2 & 4",
                syllabus_unit="Unit I & II",
                script_file="02_run_cleaning.py",
                description="Validates bounds, computes IQR and Z-Score outlier flags, saves curated parquet.",
                depends_on=["01_SOURCE_AUDIT"],
                inputs=[StageCheckpoint("data/raw/covtype.csv")],
                outputs=[
                    StageCheckpoint("data/processed/covtype_clean.parquet", min_size_bytes=1000000),
                    StageCheckpoint("reports/data_quality/outlier_comparison.csv"),
                ],
            ),
            PipelineStage(
                stage_id="03_SYNTHETIC_CLEANING_DEMO",
                name="Controlled Synthetic 800-Cell Missing Value Experiment",
                practical_id="Practical 2",
                syllabus_unit="Unit I",
                script_file="03_synthetic_cleaning_demo.py",
                description="Injects exactly 800 missing cells into continuous predictors and validates median imputation.",
                depends_on=["02_DATA_CLEANING"],
                inputs=[StageCheckpoint("data/processed/covtype_clean.parquet")],
                outputs=[
                    StageCheckpoint("data/processed/covtype_missing_values_demo_clean.csv"),
                    StageCheckpoint("reports/data_quality/synthetic_demo_audit.json"),
                ],
            ),
            PipelineStage(
                stage_id="04_DESCRIPTIVE_STATISTICS",
                name="Descriptive Statistics, Five-Number Summary & Moments",
                practical_id="Practical 3",
                syllabus_unit="Unit II",
                script_file="05_descriptive_statistics.py",
                description="Computes Five-Number Summary, mean, std, midrange, and skewness for continuous predictors.",
                depends_on=["02_DATA_CLEANING"],
                inputs=[StageCheckpoint("data/processed/covtype_clean.parquet")],
                outputs=[
                    StageCheckpoint("reports/statistics/five_number_summary.csv"),
                    StageCheckpoint("reports/statistics/descriptive_statistics.csv"),
                ],
            ),
            PipelineStage(
                stage_id="05_PREPROCESSING_EXPERIMENTS",
                name="Data Smoothing, Normalization, Discretization & Redundancy",
                practical_id="Practical 10",
                syllabus_unit="Unit IV",
                script_file="06_preprocessing_experiments.py",
                description="Compares Min-Max vs Z-Score, Gaussian smoothing, 5-bin partitioning, Chi-square & Pearson.",
                depends_on=["02_DATA_CLEANING"],
                inputs=[StageCheckpoint("data/processed/covtype_clean.parquet")],
                outputs=[
                    StageCheckpoint("reports/statistics/preprocessing_comparison.csv"),
                    StageCheckpoint("reports/statistics/pearson_correlation.csv"),
                    StageCheckpoint("reports/statistics/chi2_scores.csv"),
                ],
            ),
            PipelineStage(
                stage_id="06_FEATURE_SELECTION_PCA",
                name="Dimensionality Reduction (PCA) & Feature Selection",
                practical_id="Practical 6",
                syllabus_unit="Unit IV",
                script_file="07_feature_selection_pca.py",
                description="Reduces 10 continuous predictors to 8 components retaining 96.9% variance; ranks features.",
                depends_on=["02_DATA_CLEANING"],
                inputs=[StageCheckpoint("data/processed/covtype_clean.parquet")],
                outputs=[
                    StageCheckpoint("reports/statistics/pca_report.json"),
                    StageCheckpoint("models/pca_model.joblib"),
                ],
            ),
            PipelineStage(
                stage_id="07_CLASSIFICATION_TRAINING",
                name="Leakage-Safe Classification Model Development",
                practical_id="Practical 7",
                syllabus_unit="Unit IV",
                script_file="08_train_classifiers.py",
                description="Trains and serializes Random Forest (93.5% acc) and Decision Tree on 70/15/15 stratified split.",
                depends_on=["02_DATA_CLEANING"],
                inputs=[StageCheckpoint("data/processed/covtype_clean.parquet")],
                outputs=[
                    StageCheckpoint("models/random_forest.joblib", min_size_bytes=100000),
                    StageCheckpoint("models/decision_tree.joblib", min_size_bytes=100000),
                    StageCheckpoint("reports/statistics/classification_metrics.json"),
                ],
            ),
            PipelineStage(
                stage_id="08_CLUSTERING_ANALYSIS",
                name="Unsupervised Topographic K-Means Clustering",
                practical_id="Practical 8",
                syllabus_unit="Unit IV",
                script_file="09_run_clustering.py",
                description="Computes k=2..10 elbow/silhouette scores and extracts 4 terrain cluster profiles.",
                depends_on=["02_DATA_CLEANING"],
                inputs=[StageCheckpoint("data/processed/covtype_clean.parquet")],
                outputs=[
                    StageCheckpoint("reports/statistics/cluster_profiles.csv"),
                    StageCheckpoint("reports/statistics/cluster_elbow_silhouette.csv"),
                ],
            ),
            PipelineStage(
                stage_id="09_FIRES_REGRESSION",
                name="Pattern Analysis & Forest Fires Burned Area Regression",
                practical_id="Practical 9",
                syllabus_unit="Unit IV",
                script_file="10_train_fires_regression.py",
                description="Evaluates Ridge, Linear, and Random Forest regressors on UCI Forest Fires (log1p area).",
                depends_on=[],
                inputs=[StageCheckpoint("data/external/forestfires.csv")],
                outputs=[StageCheckpoint("reports/statistics/forest_fires_regression_summary.json")],
            ),
            PipelineStage(
                stage_id="10_EDA_VISUALIZATIONS",
                name="Exploratory Visualizations & Figure Generation",
                practical_id="Practical 5",
                syllabus_unit="Units III & V",
                script_file="04_generate_eda.py",
                description="Renders 18 publication-quality figures: treemaps, radial plots, heatmaps, boxplots, scatters.",
                depends_on=["02_DATA_CLEANING"],
                inputs=[StageCheckpoint("data/processed/covtype_clean.parquet")],
                outputs=[
                    StageCheckpoint("reports/figures/treemap_cover_type.png"),
                    StageCheckpoint("reports/figures/radial_cover_distribution.png"),
                    StageCheckpoint("reports/figures/confusion_matrix_random_forest.png"),
                ],
            ),
            PipelineStage(
                stage_id="11_INTEGRATION_EXPORTS",
                name="KNIME & Tableau Integration Payload Generator",
                practical_id="Practical 4, 6 & 10",
                syllabus_unit="Unit V",
                script_file="11_export_integrations.py",
                description="Generates 10 standard CSV exports for KNIME workflows and 8 extracts for Tableau dashboards.",
                depends_on=["02_DATA_CLEANING"],
                inputs=[StageCheckpoint("data/processed/covtype_clean.parquet")],
                outputs=[
                    StageCheckpoint("exports/knime/covertype_curated.csv"),
                    StageCheckpoint("exports/tableau/wildfire_screening_aggregates.csv"),
                ],
            ),
            PipelineStage(
                stage_id="12_ROUNDTRIP_AUDIT",
                name="KNIME, Tableau & Supabase Round-Trip Integration Audit",
                practical_id="Practicals 1-10",
                syllabus_unit="Units I-V",
                script_file="13_sync_knime_tableau_results.py",
                description="Audits bidirectional inputs/outputs and checks statistical parity within <=2.0% delta.",
                depends_on=["07_CLASSIFICATION_TRAINING", "11_INTEGRATION_EXPORTS"],
                inputs=[
                    StageCheckpoint("exports/knime/covertype_curated.csv"),
                    StageCheckpoint("exports/knime_outputs/knime_classification_metrics.csv"),
                ],
                outputs=[StageCheckpoint("reports/knime_tableau_integration_report.json")],
            ),
        ]

    def execute_all(self, fast_mode: bool = False) -> Dict[str, Any]:
        """Execute all stages sequentially, verifying checkpoints at every step."""
        logger.info("=== Starting Master Pipeline Execution (DAG has %d stages) ===", len(self.stages))
        t_start = time.perf_counter()
        manifest_stages = []
        pipeline_success = True

        for idx, stage in enumerate(self.stages, 1):
            print(f"\n[Stage {idx:02d}/{len(self.stages):02d}] {stage.name} ({stage.practical_id})")
            success = stage.run(fast_mode=fast_mode)
            manifest_stages.append({
                "stage_id": stage.stage_id,
                "name": stage.name,
                "practical_id": stage.practical_id,
                "syllabus_unit": stage.syllabus_unit,
                "script_file": stage.script_file,
                "status": stage.status,
                "duration_sec": stage.duration_sec,
                "executed_at": stage.executed_at,
                "error": stage.error_message,
            })

            if not success:
                logger.error("Pipeline halted at Stage %s", stage.stage_id)
                pipeline_success = False
                break

        total_duration = round(time.perf_counter() - t_start, 2)
        manifest = {
            "pipeline_run_id": f"run_{int(time.time())}",
            "status": "SUCCESS" if pipeline_success else "FAILED",
            "total_duration_sec": total_duration,
            "completed_stages": sum(1 for s in manifest_stages if s["status"] == "SUCCESS"),
            "total_stages": len(self.stages),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "stages": manifest_stages,
        }

        # Save manifest to reports/
        manifest_path = PROJECT_ROOT / "reports" / "pipeline_run_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        logger.info("Pipeline completed with status %s in %.2fs. Manifest: %s", manifest["status"], total_duration, manifest_path)
        return manifest

    def validate_existing_artifacts(self) -> Dict[str, Any]:
        """Quickly validate that all pipeline stage checkpoints exist and are sound without re-running."""
        validation_results = []
        all_sound = True

        for stage in self.stages:
            inputs_ok = all(inp.verify() for inp in stage.inputs)
            outputs_ok = all(out.verify() for out in stage.outputs)
            sound = inputs_ok and outputs_ok
            if not sound:
                all_sound = False
            validation_results.append({
                "stage_id": stage.stage_id,
                "name": stage.name,
                "practical_id": stage.practical_id,
                "syllabus_unit": stage.syllabus_unit,
                "inputs_verified": inputs_ok,
                "outputs_verified": outputs_ok,
                "status": "VALIDATED" if sound else "MISSING_ARTIFACTS",
            })

        return {
            "all_stages_validated": all_sound,
            "total_stages": len(self.stages),
            "validated_count": sum(1 for v in validation_results if v["status"] == "VALIDATED"),
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "stages": validation_results,
        }

    def get_dag_topology(self) -> Dict[str, Any]:
        """Returns nodes and directed dependency edges for visual pipeline DAG rendering."""
        nodes = []
        edges = []

        for stage in self.stages:
            inputs_verified = all(inp.verify() for inp in stage.inputs)
            outputs_verified = all(out.verify() for out in stage.outputs)
            nodes.append({
                "id": stage.stage_id,
                "name": stage.name,
                "practical_id": stage.practical_id,
                "syllabus_unit": stage.syllabus_unit,
                "script_file": stage.script_file,
                "description": stage.description,
                "depends_on": stage.depends_on,
                "inputs_verified": inputs_verified,
                "outputs_verified": outputs_verified,
                "status": "VALIDATED" if (inputs_verified and outputs_verified) else "PENDING",
                "inputs": [inp.artifact_path for inp in stage.inputs],
                "outputs": [out.artifact_path for out in stage.outputs],
            })
            for parent in stage.depends_on:
                edges.append({
                    "from": parent,
                    "to": stage.stage_id,
                })

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes": nodes,
            "edges": edges,
        }


# Global pipeline instance
pipeline_dag = PipelineDAG()
