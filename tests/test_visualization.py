"""Tests for the timeline PNG renderer."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.visualization import render_timeline_png


def test_renders_png():
    timeline = [
        {"label": "R_伸手", "start_s": 0.0, "end_s": 2.0},
        {"label": "A_装配", "start_s": 2.0, "end_s": 6.0},
        {"label": "Wait_等待", "start_s": 6.0, "end_s": 8.0},
    ]
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "tl.png"
        result = render_timeline_png(timeline, out, total_seconds=8.0)
        assert result is not None, "expected a PNG path"
        assert Path(result).exists() and Path(result).stat().st_size > 0
    print("renders-png OK")


def test_empty_returns_none():
    with tempfile.TemporaryDirectory() as d:
        assert render_timeline_png([], Path(d) / "x.png") is None
    print("empty-none OK")


def main() -> None:
    test_renders_png()
    test_empty_returns_none()
    print("时间轴图测试通过")


if __name__ == "__main__":
    main()
