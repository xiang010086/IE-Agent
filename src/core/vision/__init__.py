"""Pluggable vision pipelines for single-station analysis.

This package is the "heart" of the product: it turns a video into an action
sequence + timing. Every pipeline returns the same station-result dict, so the
downstream line metrics / report / validation / UI never change.

Pipelines:
- HeuristicEstimatePipeline: deterministic estimate from video duration only.
  Honest fallback when no real vision is available. NOT real recognition.
- HandsYoloPipeline: real MediaPipe Hands (Tasks API) + YOLO object detection.

Use ``get_vision_pipeline(station, config)`` to pick the right one.
"""

from __future__ import annotations

from .factory import get_vision_pipeline
from .frame_signal import FrameSignal
from .base import VisionPipeline

__all__ = ["FrameSignal", "VisionPipeline", "get_vision_pipeline"]
