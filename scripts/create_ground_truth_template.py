from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.project_manager import ProjectManager
from src.core.validation import AccuracyValidator


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a manual labeling CSV template.")
    parser.add_argument("project_id")
    args = parser.parse_args()

    manager = ProjectManager(ROOT / "data" / "projects")
    path = AccuracyValidator(manager).create_ground_truth_template(args.project_id)
    print(path)


if __name__ == "__main__":
    main()
