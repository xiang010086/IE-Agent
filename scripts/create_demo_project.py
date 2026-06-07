from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.concurrent_analyzer import ConcurrentAnalyzer
from src.core.project_manager import ProjectManager
from src.report.line_report_generator import LineReportGenerator


def main() -> None:
    manager = ProjectManager(ROOT / "data" / "projects")
    config = manager.create_project(
        "手机装配产线效率改善-演示",
        client="内部验证",
        lbr_target=85.0,
        concurrency=2,
    )
    project_id = config["project"]["id"]
    manager.add_manual_station(project_id, "工位1-元件安装", cycle_time=38, wait_time=4)
    manager.add_manual_station(project_id, "工位2-焊接固定", cycle_time=52, wait_time=8)
    manager.add_manual_station(project_id, "工位3-外观检查", cycle_time=31, wait_time=3)
    manager.add_manual_station(project_id, "工位4-包装贴标", cycle_time=44, wait_time=6)

    summary = ConcurrentAnalyzer(manager).analyze_project(project_id)
    outputs = LineReportGenerator(manager).generate(project_id, use_ai=False)

    print(f"项目ID: {project_id}")
    print(f"LBR: {summary['line_metrics']['lbr']}%")
    print(f"瓶颈: {summary['line_metrics']['bottleneck']['station_name']}")
    print(f"PDF: {outputs['pdf']}")
    print(f"CSV: {outputs['csv']}")


if __name__ == "__main__":
    main()
