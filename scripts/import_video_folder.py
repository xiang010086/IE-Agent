from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.concurrent_analyzer import ConcurrentAnalyzer
from src.core.project_manager import ProjectManager, VIDEO_EXTENSIONS
from src.report.line_report_generator import LineReportGenerator


def find_videos(folder: Path) -> list[Path]:
    return sorted(
        path
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="导入一个文件夹里的测试视频并生成分析报告。")
    parser.add_argument("folder", help="视频所在文件夹，可包含子文件夹")
    parser.add_argument("--name", default="测试视频产线分析", help="项目名称")
    parser.add_argument("--client", default="测试视频", help="客户/部门")
    parser.add_argument("--lbr-target", type=float, default=85.0, help="目标LBR")
    parser.add_argument("--concurrency", type=int, default=2, help="并发数")
    args = parser.parse_args()

    source_folder = Path(args.folder).resolve()
    videos = find_videos(source_folder)
    if not videos:
        raise SystemExit(f"没有找到视频文件：{source_folder}")

    manager = ProjectManager(ROOT / "data" / "projects")
    config = manager.create_project(
        args.name,
        client=args.client,
        lbr_target=args.lbr_target,
        concurrency=args.concurrency,
    )
    project_id = config["project"]["id"]

    for index, video in enumerate(videos, start=1):
        manager.import_video(project_id, video, station_name=f"工位{index}-{video.stem[:8]}")

    summary = ConcurrentAnalyzer(manager).analyze_project(project_id)
    outputs = LineReportGenerator(manager).generate(project_id, use_ai=False)

    print(f"项目ID: {project_id}")
    print(f"导入视频数: {len(videos)}")
    print(f"LBR: {summary['line_metrics']['lbr']}%")
    print(f"瓶颈工位: {summary['line_metrics']['bottleneck']['station_name']}")
    print(f"项目目录: {manager.get_paths(project_id).root}")
    print(f"PDF报告: {outputs['pdf']}")
    print(f"CSV数据: {outputs['csv']}")


if __name__ == "__main__":
    main()
