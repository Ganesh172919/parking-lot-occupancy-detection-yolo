from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _parse_class_ids(raw_value: str) -> tuple[int, ...]:
    class_ids: list[int] = []

    for item in raw_value.split(","):
        cleaned = item.strip()
        if not cleaned:
            continue
        class_ids.append(int(cleaned))

    return tuple(class_ids or [2])


@dataclass(frozen=True)
class Settings:
    app_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1])
    model_name: str = field(default_factory=lambda: os.getenv("YOLO_MODEL", "yolov8n.pt"))
    detection_confidence: float = field(
        default_factory=lambda: float(os.getenv("DETECTION_CONFIDENCE", "0.25"))
    )
    occupancy_threshold: float = field(
        default_factory=lambda: float(os.getenv("SLOT_OCCUPANCY_THRESHOLD", "0.20"))
    )
    camera_read_attempts: int = field(
        default_factory=lambda: int(os.getenv("CAMERA_READ_ATTEMPTS", "12"))
    )
    camera_warmup_frames: int = field(
        default_factory=lambda: int(os.getenv("CAMERA_WARMUP_FRAMES", "5"))
    )
    target_class_ids: tuple[int, ...] = field(
        default_factory=lambda: _parse_class_ids(os.getenv("TARGET_CLASS_IDS", "2"))
    )

    @property
    def static_dir(self) -> Path:
        return self.app_dir / "static"

    @property
    def slot_config_path(self) -> Path:
        return self.app_dir / "config" / "parking_slots.json"

