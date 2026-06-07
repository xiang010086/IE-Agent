from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.project_manager import ProjectManager
from src.core.validation import AccuracyValidator, ValidationThresholds


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate analyzer output against manual ground truth.")
    parser.add_argument("project_id")
    parser.add_argument("ground_truth_csv")
    parser.add_argument("--action-tolerance", type=int, default=2)
    parser.add_argument("--cycle-tolerance-pct", type=float, default=10.0)
    parser.add_argument("--wait-tolerance-pct", type=float, default=20.0)
    args = parser.parse_args()

    manager = ProjectManager(ROOT / "data" / "projects")
    thresholds = ValidationThresholds(
        action_count_tolerance=args.action_tolerance,
        cycle_time_tolerance_pct=args.cycle_tolerance_pct,
        wait_time_tolerance_pct=args.wait_tolerance_pct,
    )
    report = AccuracyValidator(manager).validate(args.project_id, args.ground_truth_csv, thresholds)
    print(f"Validated stations: {report['summary']['validated_station_count']}")
    print(f"Pass rate: {report['summary']['pass_rate_pct']}%")
    print(f"Action count accuracy: {report['summary']['action_count_accuracy_pct']}%")
    print(manager.get_paths(args.project_id).exports / "validation_report.json")


if __name__ == "__main__":
    main()
