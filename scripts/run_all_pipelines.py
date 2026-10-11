"""Master Pipeline Orchestrator CLI.

Executes the complete Forest Cover Type & Wildfire-Risk Analysis pipeline
using the structured PipelineDAG execution engine.

Usage:
    python scripts/run_all_pipelines.py               # Run full staged pipeline DAG
    python scripts/run_all_pipelines.py --validate    # Validate all stage artifacts without re-running
    python scripts/run_all_pipelines.py --fast        # Run fast pipeline mode
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from python_src.logging_config import get_logger, setup_logging
from python_src.pipeline import pipeline_dag

setup_logging()
logger = get_logger("pipeline_runner")


def main() -> int:
    parser = argparse.ArgumentParser(description="Master Analytics Pipeline Orchestrator")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate all stage checkpoints and artifact files without re-executing heavy computation",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Execute pipeline in fast mode",
    )
    args = parser.parse_args()

    print("=" * 80)
    print(" FOREST COVER TYPE & WILDFIRE-RISK ANALYSIS: PIPELINE ORCHESTRATOR")
    print("=" * 80)

    if args.validate:
        print("\n--> Mode: VALIDATION CHECKPOINT AUDIT ONLY")
        res = pipeline_dag.validate_existing_artifacts()
        for s in res["stages"]:
            status_icon = "[PASS]" if s["status"] == "VALIDATED" else "[FAIL]"
            print(f"{status_icon} {s['stage_id']:<26} | {s['practical_id']:<14} | {s['status']}")
        print("=" * 80)
        print(f"Artifact Validation: {res['validated_count']}/{res['total_stages']} Stages Passed.")
        return 0 if res["all_stages_validated"] else 1

    # Execute full pipeline
    print("\n--> Mode: FULL SEQUENTIAL DAG EXECUTION")
    manifest = pipeline_dag.execute_all(fast_mode=args.fast)

    print("\n" + "=" * 80)
    print(" PIPELINE EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Run Status:       {manifest['status']}")
    print(f"Total Duration:   {manifest['total_duration_sec']}s")
    print(f"Completed Stages: {manifest['completed_stages']}/{manifest['total_stages']}")
    print(f"Run Manifest:     reports/pipeline_run_manifest.json")
    print("=" * 80)

    return 0 if manifest["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    sys.exit(main())
