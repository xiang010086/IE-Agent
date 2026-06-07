from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

# torch (via ultralytics) and mediapipe both bundle an OpenMP runtime; on
# Windows + Anaconda they clash (OMP Error #15). Allow the duplicate so both
# can load. Safe for inference workloads. Must be set before importing either.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from .actions import ClassifierParams, classify
from .base import VisionPipeline
from .frame_signal import FrameSignal, ObjectBox

# Landmark indices whose mean approximates the palm center (wrist + finger MCPs).
_PALM_LANDMARKS = (0, 5, 9, 13, 17)
_YOLO_MIN_CONF = 0.30


def dependencies_available() -> tuple[bool, str]:
    """Check that mediapipe Tasks + ultralytics + cv2 import. Returns (ok, reason)."""
    try:
        import cv2  # noqa: F401
        import mediapipe  # noqa: F401
        from mediapipe.tasks.python import vision  # noqa: F401
        from ultralytics import YOLO  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment dependent
        return False, f"缺少视觉依赖: {exc!r}"
    return True, ""


class HandsYoloPipeline(VisionPipeline):
    """Real top-down recognition: MediaPipe Hands (Tasks API) + YOLO objects.

    Produces a genuine FrameSignal sequence and classifies it into MTM actions,
    so results vary with the video (unlike the heuristic estimate). YOLO uses a
    generic COCO-pretrained model here; industrial part/bin detection needs a
    custom-trained model later — object boxes are anchors, not ground truth.
    """

    analysis_mode = "vision_handsyolo"

    def __init__(
        self,
        hand_model: str,
        yolo_model: str,
        mtm_standard: str = "MTM-1",
        sample_rate: int = 5,
        min_hand_confidence: float = 0.3,
        classifier_params: ClassifierParams | None = None,
    ) -> None:
        super().__init__(mtm_standard)
        self.hand_model = hand_model
        self.yolo_model = yolo_model
        self.sample_rate = max(1, int(sample_rate))
        # Lower this (e.g. 0.2) to recover detections on low-resolution footage.
        self.min_hand_confidence = float(min_hand_confidence)
        self.classifier_params = classifier_params or ClassifierParams()

    # -- model construction (lazy, per analyze call) -------------------

    def _build_landmarker(self):
        import mediapipe as mp
        from mediapipe.tasks import python as mpy
        from mediapipe.tasks.python import vision

        options = vision.HandLandmarkerOptions(
            base_options=mpy.BaseOptions(model_asset_path=self.hand_model),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=self.min_hand_confidence,
            min_hand_presence_confidence=self.min_hand_confidence,
            min_tracking_confidence=self.min_hand_confidence,
        )
        return mp, vision, vision.HandLandmarker.create_from_options(options)

    def _build_yolo(self):
        from ultralytics import YOLO

        return YOLO(self.yolo_model)

    # -- core ----------------------------------------------------------

    def extract_signals(self, video_path: Path) -> tuple[list[FrameSignal], dict[str, Any]]:
        import cv2

        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise RuntimeError(f"无法打开视频: {video_path}")
        fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
        frame_total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if fps <= 0:
            fps = 25.0  # reasonable default if metadata missing

        mp, _vision, landmarker = self._build_landmarker()
        yolo = self._build_yolo()

        signals: list[FrameSignal] = []
        hand_hits = 0
        frame_index = -1
        last_ts = -1
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                frame_index += 1
                if frame_index % self.sample_rate != 0:
                    continue

                ts = int(frame_index / fps * 1000)
                if ts <= last_ts:
                    ts = last_ts + 1
                last_ts = ts

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                signal = FrameSignal(frame_index=frame_index, timestamp_ms=float(ts), source="hands_yolo")

                # --- hands ---
                try:
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                    hand_res = landmarker.detect_for_video(mp_image, ts)
                    if hand_res.hand_landmarks:
                        confs = []
                        for idx, lms in enumerate(hand_res.hand_landmarks):
                            cx = sum(lms[i].x for i in _PALM_LANDMARKS) / len(_PALM_LANDMARKS)
                            cy = sum(lms[i].y for i in _PALM_LANDMARKS) / len(_PALM_LANDMARKS)
                            signal.hand_positions.append((cx, cy))
                            if hand_res.handedness and idx < len(hand_res.handedness):
                                confs.append(hand_res.handedness[idx][0].score)
                        signal.hand_confidence = max(confs) if confs else 1.0
                        hand_hits += 1
                except Exception:
                    pass

                # --- objects (YOLO) ---
                try:
                    h, w = rgb.shape[:2]
                    yres = yolo.predict(frame, verbose=False)
                    for r in yres:
                        names = r.names
                        for box in r.boxes:
                            conf = float(box.conf[0])
                            if conf < _YOLO_MIN_CONF:
                                continue
                            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
                            cls = int(box.cls[0])
                            signal.object_boxes.append(
                                ObjectBox(x1 / w, y1 / h, x2 / w, y2 / h, names.get(cls, str(cls)), conf)
                            )
                except Exception:
                    pass

                signals.append(signal)
        finally:
            capture.release()
            try:
                landmarker.close()
            except Exception:
                pass

        meta = {
            "fps": round(fps, 2),
            "frames_total": frame_total,
            "frames_sampled": len(signals),
            "sample_rate": self.sample_rate,
            "hand_detection_rate": round(hand_hits / len(signals), 3) if signals else 0.0,
        }
        return signals, meta

    def analyze(
        self,
        station: dict[str, Any],
        video_path: Path | None,
        tuning: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        if video_path is None or not Path(video_path).exists():
            return self.error_result(station, "视觉分析需要可读取的视频文件。")

        try:
            signals, meta = self.extract_signals(Path(video_path))
        except Exception as exc:
            return self.error_result(station, f"视觉分析失败: {exc!r}")

        duration = self.read_video_duration(video_path) or (
            signals[-1].timestamp_ms / 1000.0 if signals else 0.0
        )
        # A manual cycle override still wins (one video may hold several cycles).
        manual_cycle = station.get("cycle_time")
        total_cycle_time = max(1.0, float(manual_cycle)) if manual_cycle else max(0.1, duration)

        from .actions import segments_to_timeline

        segments, summary = classify(signals, self.classifier_params)

        extra = {
            "vision_meta": meta,
            "object_detection_note": "YOLO 为 COCO 通用预训练，未识别工业件；物体框仅作动作锚点。",
        }
        return self.assemble_result(
            station,
            total_cycle_time=total_cycle_time,
            wait_time=summary["wait_time"],
            action_count=summary["action_count"],
            action_breakdown=summary["breakdown"],
            runtime_seconds=time.perf_counter() - started,
            action_timeline=segments_to_timeline(segments),
            extra=extra,
        )
