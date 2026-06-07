"""Tests for the vision pipeline.

- Classifier unit test: deterministic, no heavy deps. Proves the action output
  genuinely varies with the input signal (the anti-"synthetic numbers" property).
- Pipeline smoke test: runs the real Hands+YOLO pipeline if deps + models are
  present, otherwise skips. Asserts it is labelled as real recognition.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.vision.actions import WORK_LABELS, classify
from src.core.vision.frame_signal import FrameSignal, ObjectBox


def _static_sequence(n: int = 20) -> list[FrameSignal]:
    """Hand parked in a corner, no objects -> should read as Wait."""
    return [
        FrameSignal(frame_index=i, timestamp_ms=i * 100.0, hand_positions=[(0.1, 0.1)], hand_confidence=0.9)
        for i in range(n)
    ]


def _active_sequence() -> list[FrameSignal]:
    """Hand sweeps toward a centered object then settles on it."""
    obj = ObjectBox(0.45, 0.45, 0.55, 0.55, "object", 0.9)
    signals: list[FrameSignal] = []
    # Phase 1: move fast from left toward the object.
    for i in range(8):
        x = 0.1 + (0.4 * i / 7)
        signals.append(
            FrameSignal(frame_index=i, timestamp_ms=i * 100.0, hand_positions=[(x, 0.5)],
                        hand_confidence=0.9, object_boxes=[obj])
        )
    # Phase 2: settle on the object in the centre (low speed, near, centred).
    for j in range(8, 18):
        signals.append(
            FrameSignal(frame_index=j, timestamp_ms=j * 100.0, hand_positions=[(0.5, 0.5)],
                        hand_confidence=0.9, object_boxes=[obj])
        )
    return signals


def test_classifier_varies_with_input() -> None:
    _, static_summary = classify(_static_sequence())
    segments, active_summary = classify(_active_sequence())

    # Static => no work actions; active => some work actions. The whole point:
    # output depends on the signal, not on a fixed formula.
    assert static_summary["action_count"] == 0, static_summary
    assert active_summary["action_count"] >= 1, active_summary
    assert active_summary["breakdown"] != static_summary["breakdown"]
    assert any(seg.label in WORK_LABELS for seg in segments)
    print(f"classifier OK: static={static_summary['action_count']} active={active_summary['action_count']}")


def test_pipeline_smoke() -> None:
    from src.core.vision.hands_yolo import HandsYoloPipeline, dependencies_available

    ok, reason = dependencies_available()
    hand_model = ROOT / "data" / "models" / "hand_landmarker.task"
    yolo_model = ROOT / "data" / "models" / "yolov8n.pt"
    video = ROOT / "data" / "projects" / "proj_20260526_095403" / "videos" / "station_01.mp4"
    if not (ok and hand_model.exists() and yolo_model.exists() and video.exists()):
        print(f"pipeline smoke SKIPPED ({reason or 'models/video missing'})")
        return

    pipeline = HandsYoloPipeline(str(hand_model), str(yolo_model), sample_rate=15)
    station = {"id": "s", "name": "t", "video_file": "station_01.mp4", "view_type": "top_down"}
    result = pipeline.analyze(station, video)

    assert result["analysis_mode"] == "vision_handsyolo", result
    assert result["cycle_time_metrics"]["total_cycle_time"] > 0
    assert result["vision_meta"]["frames_sampled"] > 0
    print(f"pipeline smoke OK: sampled={result['vision_meta']['frames_sampled']} "
          f"handrate={result['vision_meta']['hand_detection_rate']}")


def test_segments_to_timeline() -> None:
    from src.core.vision.actions import ActionSegment, segments_to_timeline

    segs = [ActionSegment("R_伸手", 0.0, 1000.0), ActionSegment("Wait_等待", 1000.0, 3000.0)]
    tl = segments_to_timeline(segs)
    assert tl == [
        {"label": "R_伸手", "start_s": 0.0, "end_s": 1.0},
        {"label": "Wait_等待", "start_s": 1.0, "end_s": 3.0},
    ]
    assert segments_to_timeline([]) == []
    print("segments_to_timeline OK")


def test_assemble_result_carries_timeline() -> None:
    from src.core.vision.heuristic import HeuristicEstimatePipeline

    p = HeuristicEstimatePipeline()
    station = {"id": "s", "name": "t", "video_file": "x.mp4"}
    timeline = [{"label": "R_伸手", "start_s": 0.0, "end_s": 1.0}]
    r = p.assemble_result(
        station, total_cycle_time=10.0, wait_time=2.0, action_count=1,
        action_breakdown={"R_伸手": 1.0}, runtime_seconds=0.1, action_timeline=timeline,
    )
    assert r["action_timeline"] == timeline
    r2 = p.assemble_result(
        station, total_cycle_time=10.0, wait_time=2.0, action_count=1,
        action_breakdown={}, runtime_seconds=0.1,
    )
    assert r2["action_timeline"] == []
    print("assemble_result timeline OK")


def main() -> None:
    test_classifier_varies_with_input()
    test_segments_to_timeline()
    test_assemble_result_carries_timeline()
    test_pipeline_smoke()
    print("视觉测试通过")


if __name__ == "__main__":
    main()
