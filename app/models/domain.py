from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Detection:
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    class_id: int
    label: str


@dataclass(frozen=True)
class ParkingSlot:
    id: str
    x: int
    y: int
    width: int
    height: int

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.width, self.y + self.height)


@dataclass(frozen=True)
class SlotEvaluation:
    slot: ParkingSlot
    occupied: bool
    overlap: float


@dataclass(frozen=True)
class OccupancyCounts:
    total_slots: int
    occupied_slots: int
    free_slots: int

