"""Download the vision models needed by HandsYoloPipeline.

    python scripts/download_models.py

Fetches:
- hand_landmarker.task        (MediaPipe Hands, Tasks API)
- pose_landmarker_lite.task   (MediaPipe Pose, used by the diagnostic for comparison)
- yolov8n.pt                  (ultralytics YOLO, generic COCO detector)

Models land in data/models/ and are git-ignored (not committed).
"""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "data" / "models"

HAND_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
POSE_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)
YOLO_MODEL = "yolov8n.pt"


def _download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[skip] {dest.name} already exists ({dest.stat().st_size} bytes)")
        return
    print(f"[download] {url}\n        -> {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    print(f"[done] {dest.name} ({dest.stat().st_size} bytes)")


def _fetch_yolo(dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"[skip] {dest.name} already exists")
        return
    # ultralytics downloads the weight on construction; then move it next to the others.
    from ultralytics import YOLO

    print(f"[download] {YOLO_MODEL} via ultralytics")
    model = YOLO(YOLO_MODEL)  # downloads to cwd/cache
    src = Path(getattr(model, "ckpt_path", "") or YOLO_MODEL)
    if src.exists() and src.resolve() != dest.resolve():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())
    print(f"[done] {dest.name}")


def main() -> int:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        _download(HAND_LANDMARKER_URL, MODELS_DIR / "hand_landmarker.task")
        _download(POSE_LANDMARKER_URL, MODELS_DIR / "pose_landmarker_lite.task")
        _fetch_yolo(MODELS_DIR / YOLO_MODEL)
    except Exception as exc:  # pragma: no cover - network dependent
        print(f"[error] {exc!r}")
        return 1
    print(f"\nModels ready in: {MODELS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
