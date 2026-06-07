"""Vision diagnostic for a single video.

    python scripts/diagnose_vision.py <video.mp4> [--stride 2] [--out out_dir]

Runs MediaPipe Hands AND Pose (Tasks API) plus YOLO on the same video and draws
everything back onto the frames, so you can decide by eye which signal to trust
for your camera angle (top-down work cells usually => Hands reliable, Pose flaky).

Outputs (in --out, default next to the video):
- annotated_output.mp4   white dots = Pose, colored 21-pt = Hands, boxes = YOLO
- wrist_speed.png         hand speed curve over time
- prints reliability stats + a recommendation
"""

from __future__ import annotations

import argparse
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "data" / "models"

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17),
]
HAND_COLORS = [(0, 255, 0), (0, 165, 255)]  # BGR: green, orange
_PALM = (0, 5, 9, 13, 17)


def build_hands(model_path: Path):
    import mediapipe as mp
    from mediapipe.tasks import python as mpy
    from mediapipe.tasks.python import vision

    opt = vision.HandLandmarkerOptions(
        base_options=mpy.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.3,
    )
    return mp, vision.HandLandmarker.create_from_options(opt)


def build_pose(model_path: Path):
    if not model_path.exists():
        return None
    from mediapipe.tasks import python as mpy
    from mediapipe.tasks.python import vision

    opt = vision.PoseLandmarkerOptions(
        base_options=mpy.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
    )
    return vision.PoseLandmarker.create_from_options(opt)


def main() -> int:
    parser = argparse.ArgumentParser(description="Vision diagnostic (Hands+Pose+YOLO)")
    parser.add_argument("video", help="path to the video file")
    parser.add_argument("--stride", type=int, default=2, help="run inference every N frames")
    parser.add_argument("--out", default=None, help="output directory")
    args = parser.parse_args()

    import cv2

    video_path = Path(args.video)
    if not video_path.exists():
        print(f"[error] video not found: {video_path}")
        return 1
    out_dir = Path(args.out) if args.out else video_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    hand_model = MODELS / "hand_landmarker.task"
    if not hand_model.exists():
        print(f"[error] missing {hand_model}. Run scripts/download_models.py first.")
        return 1

    mp, hands = build_hands(hand_model)
    pose = build_pose(MODELS / "pose_landmarker_lite.task")
    try:
        from ultralytics import YOLO

        yolo = YOLO(str(MODELS / "yolov8n.pt")) if (MODELS / "yolov8n.pt").exists() else None
    except Exception:
        yolo = None

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer = cv2.VideoWriter(
        str(out_dir / "annotated_output.mp4"),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (w, h),
    )

    hand_hits = pose_hits = sampled = 0
    yolo_dets = 0
    speed_series: list[tuple[float, float]] = []
    last_palm = None
    last_ts = -1
    frame_index = -1
    last_draw = {"hands": [], "pose": [], "boxes": []}

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_index += 1
        run = frame_index % max(1, args.stride) == 0
        if run:
            sampled += 1
            ts = int(frame_index / fps * 1000)
            if ts <= last_ts:
                ts = last_ts + 1
            last_ts = ts
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            hands_draw = []
            try:
                hres = hands.detect_for_video(mp_img, ts)
                for lms in hres.hand_landmarks:
                    pts = [(int(p.x * w), int(p.y * h)) for p in lms]
                    hands_draw.append(pts)
                if hres.hand_landmarks:
                    hand_hits += 1
                    lms = hres.hand_landmarks[0]
                    palm = (sum(lms[i].x for i in _PALM) / 5, sum(lms[i].y for i in _PALM) / 5)
                    if last_palm is not None:
                        speed_series.append((ts / 1000.0, math.hypot(palm[0] - last_palm[0], palm[1] - last_palm[1]) * fps / max(1, args.stride)))
                    last_palm = palm
            except Exception:
                pass

            pose_draw = []
            if pose is not None:
                try:
                    pres = pose.detect_for_video(mp_img, ts)
                    for lms in pres.pose_landmarks:
                        pose_draw = [(int(p.x * w), int(p.y * h)) for p in lms]
                    if pres.pose_landmarks:
                        pose_hits += 1
                except Exception:
                    pass

            boxes = []
            if yolo is not None:
                try:
                    for r in yolo.predict(frame, verbose=False):
                        for b in r.boxes:
                            if float(b.conf[0]) < 0.3:
                                continue
                            x1, y1, x2, y2 = (int(v) for v in b.xyxy[0])
                            boxes.append((x1, y1, x2, y2, r.names.get(int(b.cls[0]), "")))
                    yolo_dets += len(boxes)
                except Exception:
                    pass

            last_draw = {"hands": hands_draw, "pose": pose_draw, "boxes": boxes}

        # Draw (carry last detections forward on skipped frames).
        for x, y in last_draw["pose"]:
            cv2.circle(frame, (x, y), 2, (255, 255, 255), -1)
        for hi, pts in enumerate(last_draw["hands"]):
            color = HAND_COLORS[hi % len(HAND_COLORS)]
            for a, b in HAND_CONNECTIONS:
                cv2.line(frame, pts[a], pts[b], color, 1)
            for p in pts:
                cv2.circle(frame, p, 3, color, -1)
        for x1, y1, x2, y2, name in last_draw["boxes"]:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.putText(frame, name, (x1, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        writer.write(frame)

    cap.release()
    writer.release()
    try:
        hands.close()
        if pose:
            pose.close()
    except Exception:
        pass

    # Speed curve.
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        if speed_series:
            xs, ys = zip(*speed_series)
            plt.figure(figsize=(10, 3))
            plt.plot(xs, ys, color="#0f766e")
            plt.xlabel("time (s)")
            plt.ylabel("hand speed (norm/s)")
            plt.title("Primary hand speed")
            plt.tight_layout()
            plt.savefig(out_dir / "wrist_speed.png", dpi=110)
            plt.close()
    except Exception as exc:
        print(f"[warn] could not draw speed curve: {exc!r}")

    hand_rate = hand_hits / sampled if sampled else 0.0
    pose_rate = pose_hits / sampled if sampled else 0.0
    print("\n==== 诊断结论 ====")
    print(f"采样帧数: {sampled}  (stride={args.stride}, fps={fps:.1f}, {w}x{h})")
    print(f"Hands 可靠率: {hand_rate:.0%}   Pose 可靠率: {pose_rate:.0%}")
    print(f"YOLO 平均每帧检测框: {yolo_dets / sampled:.2f}" if sampled else "YOLO: n/a")
    print(f"标注视频: {out_dir / 'annotated_output.mp4'}")
    if hand_rate >= pose_rate + 0.15:
        print("建议: Hands 明显更稳 → 俯视场景用 Hands+YOLO（与改进方案一致）。")
    elif pose_rate >= hand_rate + 0.15:
        print("建议: Pose 更稳 → 该机位可能更接近正面，考虑 Pose+YOLO。")
    else:
        print("建议: 两者接近，请人眼看标注视频确认关键点是否贴合再决定。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
