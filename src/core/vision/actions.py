from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from .frame_signal import FrameSignal

# MTM-style action labels produced for the top-down Hands+YOLO scenario.
REACH = "R_伸手"
GRASP = "G_抓取"
MOVE = "M_移动"
ASSEMBLE = "A_装配"
WAIT = "Wait_等待"

#: Labels that count as real work (used for action_count).
WORK_LABELS = (REACH, GRASP, MOVE, ASSEMBLE)


@dataclass
class ActionSegment:
    label: str
    start_ms: float
    end_ms: float

    @property
    def duration_s(self) -> float:
        return max(0.0, (self.end_ms - self.start_ms) / 1000.0)


@dataclass
class ClassifierParams:
    speed_enter: float = 0.15      # normalized units/sec to ENTER a moving state
    speed_exit: float = 0.06       # below this we are "slow" (hysteresis gap)
    near_object_dist: float = 0.12  # normalized distance hand<->object center => "near"
    center_radius: float = 0.22    # distance from frame center counted as work zone
    smooth_window: int = 3         # majority-vote window (odd)
    min_action_frames: int = 4     # segments shorter than this merge into neighbours


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _nearest_object_dist(hand: tuple[float, float], signal: FrameSignal) -> float:
    if not signal.object_boxes:
        return float("inf")
    return min(_dist(hand, box.center) for box in signal.object_boxes)


def _raw_label(
    signal: FrameSignal,
    speed: float | None,
    prev_label: str,
    params: ClassifierParams,
) -> str:
    """Per-frame label with hysteresis on speed."""
    hand = signal.primary_hand
    if hand is None or speed is None:
        # No reliable hand this frame -> treat as idle/waiting.
        return WAIT

    near = _nearest_object_dist(hand, signal) <= params.near_object_dist
    in_center = _dist(hand, (0.5, 0.5)) <= params.center_radius

    fast = speed >= params.speed_enter
    slow = speed <= params.speed_exit

    if fast:
        # Moving quickly: reaching toward an object vs. carrying it elsewhere.
        return REACH if near else MOVE
    if slow:
        if near and in_center:
            return ASSEMBLE
        if near:
            return GRASP
        return WAIT
    # In the hysteresis band: keep previous state to avoid flip-flopping.
    return prev_label or WAIT


def _smooth(labels: list[str], window: int) -> list[str]:
    if window <= 1 or len(labels) < window:
        return labels
    half = window // 2
    out: list[str] = []
    for i in range(len(labels)):
        lo = max(0, i - half)
        hi = min(len(labels), i + half + 1)
        chunk = labels[lo:hi]
        out.append(max(set(chunk), key=chunk.count))
    return out


def _to_segments(labels: list[str], signals: list[FrameSignal]) -> list[ActionSegment]:
    segments: list[ActionSegment] = []
    if not labels:
        return segments
    start = 0
    for i in range(1, len(labels) + 1):
        if i == len(labels) or labels[i] != labels[start]:
            seg_start_ms = signals[start].timestamp_ms
            # End at the next sample's timestamp so durations tile the timeline.
            end_idx = min(i, len(signals) - 1)
            seg_end_ms = signals[end_idx].timestamp_ms
            if i == len(labels):
                seg_end_ms = signals[-1].timestamp_ms
            segments.append(ActionSegment(labels[start], seg_start_ms, seg_end_ms))
            start = i
    return segments


def _merge_short(segments: list[ActionSegment], min_frames: int, sample_ms: float) -> list[ActionSegment]:
    """Merge segments shorter than the minimum duration into a neighbour."""
    if not segments:
        return segments
    min_ms = max(1.0, min_frames * sample_ms)
    merged = [segments[0]]
    for seg in segments[1:]:
        last = merged[-1]
        if (seg.end_ms - seg.start_ms) < min_ms:
            # Absorb the short segment into the previous one.
            last.end_ms = seg.end_ms
        elif seg.label == last.label:
            last.end_ms = seg.end_ms
        else:
            merged.append(seg)
    return merged


def classify(
    signals: list[FrameSignal],
    params: ClassifierParams | None = None,
) -> tuple[list[ActionSegment], dict[str, Any]]:
    """Turn a FrameSignal sequence into action segments + a summary.

    v1 rule-based classifier (precision is a later iteration). The point is that
    the output genuinely varies with the video instead of being a fixed formula.
    """
    params = params or ClassifierParams()
    if not signals:
        return [], {"action_count": 0, "wait_time": 0.0, "breakdown": {}}

    # Per-frame hand speed (normalized units per second) via finite differences.
    speeds: list[float | None] = [None]
    for i in range(1, len(signals)):
        prev, cur = signals[i - 1], signals[i]
        dt = (cur.timestamp_ms - prev.timestamp_ms) / 1000.0
        if prev.primary_hand and cur.primary_hand and dt > 0:
            speeds.append(_dist(prev.primary_hand, cur.primary_hand) / dt)
        else:
            speeds.append(None)

    raw: list[str] = []
    prev_label = WAIT
    for signal, speed in zip(signals, speeds):
        label = _raw_label(signal, speed, prev_label, params)
        raw.append(label)
        prev_label = label

    labels = _smooth(raw, params.smooth_window)

    # Median sample interval, for the minimum-duration merge.
    deltas = [
        signals[i].timestamp_ms - signals[i - 1].timestamp_ms
        for i in range(1, len(signals))
        if signals[i].timestamp_ms > signals[i - 1].timestamp_ms
    ]
    sample_ms = sorted(deltas)[len(deltas) // 2] if deltas else 100.0

    segments = _merge_short(_to_segments(labels, signals), params.min_action_frames, sample_ms)

    breakdown: dict[str, float] = {}
    for seg in segments:
        breakdown[seg.label] = breakdown.get(seg.label, 0.0) + seg.duration_s
    wait_time = breakdown.get(WAIT, 0.0)
    action_count = sum(1 for seg in segments if seg.label in WORK_LABELS)

    summary = {
        "action_count": action_count,
        "wait_time": wait_time,
        "breakdown": breakdown,
        "segment_count": len(segments),
    }
    return segments, summary


def segments_to_timeline(segments: list[ActionSegment]) -> list[dict[str, float | str]]:
    """Convert action segments to a UI-friendly timeline list (seconds)."""
    return [
        {"label": seg.label, "start_s": round(seg.start_ms / 1000.0, 2), "end_s": round(seg.end_ms / 1000.0, 2)}
        for seg in segments
    ]
