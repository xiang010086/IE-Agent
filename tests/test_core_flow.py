from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.concurrent_analyzer import ConcurrentAnalyzer
from src.core.project_manager import ProjectManager
from src.core.validation import AccuracyValidator
from src.report.line_report_generator import LineReportGenerator


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ProjectManager(Path(temp_dir) / "projects")
        config = manager.create_project("测试产线", "测试客户", lbr_target=85, concurrency=2)
        project_id = config["project"]["id"]

        manager.add_manual_station(project_id, "工位1-上料", 30, 3)
        manager.add_manual_station(project_id, "工位2-装配", 45, 7)
        manager.add_manual_station(project_id, "工位3-检测", 28, 2)

        analyzer = ConcurrentAnalyzer(manager)
        summary = analyzer.analyze_project(project_id)
        assert summary["line_metrics"]["station_count"] == 3
        assert summary["line_metrics"]["lbr"] > 0
        assert summary["line_metrics"]["bottleneck"]["station_name"] == "工位2-装配"

        # standard_time is now part of every station's mtm_summary
        for st in summary["stations"]:
            assert "standard_time" in st["mtm_summary"], st["mtm_summary"]

        # No project_info yet -> takt analysis skipped, but decisions still exist
        assert summary["takt_analysis"]["skipped"] is True
        assert summary["action_recommendations"], "expected at least one action verdict"

        # Provide full project-info -> takt analysis runs
        manager.save_project_info(project_id, {
            "shift_minutes": 480, "break_minutes": 60,
            "demand_per_shift": 400, "effective_rate": 0.9, "operator_count": 3,
        })
        summary2 = analyzer.analyze_project(project_id)
        takt = summary2["takt_analysis"]
        assert takt["skipped"] is False, takt
        assert takt["takt_time_s"] > 0, takt
        assert takt["required_workers"] is not None

        outputs = LineReportGenerator(manager).generate(project_id, use_ai=False)
        assert Path(outputs["pdf"]).exists()
        assert Path(outputs["csv"]).exists()
        assert Path(outputs["json"]).exists()

        # report now carries a DeepSeek/rule narrative (use_ai=False -> rule_fallback)
        import json as _json
        report = _json.loads(Path(outputs["json"]).read_text(encoding="utf-8"))
        narr = report.get("report_narrative", {})
        assert narr.get("source") == "rule_fallback", narr.get("source")
        assert narr.get("executive_summary") and narr.get("recommendations")
        assert "knowledge_used" in report and report["knowledge_used"]

        validator = AccuracyValidator(manager)
        template = validator.create_ground_truth_template(project_id)
        with template.open("r", newline="", encoding="utf-8-sig") as file:
            rows = list(csv.DictReader(file))
            fieldnames = list(rows[0].keys())
        rows[0]["ground_truth_cycle_time"] = "30"
        rows[0]["ground_truth_wait_time"] = "3"
        rows[0]["ground_truth_action_count"] = "10"
        with template.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        validation = validator.validate(project_id, template)
        assert validation["summary"]["validated_station_count"] >= 1
        assert (manager.get_paths(project_id).exports / "validation_report.csv").exists()

        print("核心流程测试通过")
        print(f"LBR={summary['line_metrics']['lbr']}%")
        print(f"PDF={outputs['pdf']}")


if __name__ == "__main__":
    main()
