from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.ui_helpers import TERMS, build_timeline_html, mode_badge


def test_terms_have_both_languages() -> None:
    for key, val in TERMS.items():
        assert "zh" in val and "en" in val and val["zh"], key


def test_build_timeline_html() -> None:
    tl = [
        {"label": "R_伸手", "start_s": 0.0, "end_s": 1.0},
        {"label": "Wait_等待", "start_s": 1.0, "end_s": 3.0},
    ]
    html = build_timeline_html(tl)
    assert "width:33.33%" in html  # 1/3 段
    assert "width:66.67%" in html  # 2/3 段
    assert build_timeline_html([]) == ""  # 空 → 空串


def test_mode_badge() -> None:
    assert "真实" in mode_badge("vision_handsyolo", "zh")
    assert "估算" in mode_badge("heuristic_estimate", "zh")
    assert "失败" in mode_badge("error", "zh")
    assert "Real" in mode_badge("vision_handsyolo", "en")


def main() -> None:
    test_terms_have_both_languages()
    test_build_timeline_html()
    test_mode_badge()
    print("ui_helpers 测试通过")


if __name__ == "__main__":
    main()
