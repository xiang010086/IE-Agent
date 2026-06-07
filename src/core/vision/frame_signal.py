from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ObjectBox:
    """A single detected object (YOLO)."""

    x1: float
    y1: float
    x2: float
    y2: float
    label: str
    confidence: float

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)


@dataclass
class FrameSignal:
    """Standardized per-frame output from any vision pipeline.

    Downstream action classification consumes only this structure, so the
    underlying model (Hands+YOLO today, Pose+YOLO tomorrow) stays invisible to
    the rest of the system. Coordinates are normalized to [0, 1] relative to
    frame width/height so they are resolution independent.
    """

    frame_index: int
    timestamp_ms: float
    # Palm centers of detected hands, normalized (x, y). May be empty.
    hand_positions: list[tuple[float, float]] = field(default_factory=list)
    # Detection confidence of the most confident hand (0..1).
    hand_confidence: float = 0.0
    # Detected objects (YOLO), normalized coordinates.
    object_boxes: list[ObjectBox] = field(default_factory=list)
    # Optional motion bounding box from background subtraction (x1, y1, x2, y2).
    motion_region: tuple[float, float, float, float] | None = None
    # Where this signal came from, for debugging ("hands_yolo", ...).
    source: str = ""

    @property
    def has_hand(self) -> bool:
        return bool(self.hand_positions)

    @property
    def primary_hand(self) -> tuple[float, float] | None:
        return self.hand_positions[0] if self.hand_positions else None
