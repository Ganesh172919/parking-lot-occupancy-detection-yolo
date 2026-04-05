from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from app.models.domain import Detection, OccupancyCounts, ParkingSlot, SlotEvaluation


class SlotConfigError(RuntimeError):
    pass


class ParkingService:
    def __init__(self, slot_config_path: Path, occupancy_threshold: float) -> None:
        self.slot_config_path = slot_config_path
        self.occupancy_threshold = occupancy_threshold

    def load_slots(self) -> list[ParkingSlot]:
        if not self.slot_config_path.exists():
            raise SlotConfigError(
                f"Slot configuration file was not found: {self.slot_config_path}"
            )

        try:
            raw_content = self.slot_config_path.read_text(encoding="utf-8")
            data = json.loads(raw_content)
        except OSError as exc:
            raise SlotConfigError(
                f"Unable to read the slot configuration file: {self.slot_config_path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise SlotConfigError(
                f"Slot configuration file contains invalid JSON: {self.slot_config_path}"
            ) from exc

        raw_slots = data.get("slots", [])

        if not raw_slots:
            raise SlotConfigError("No parking slots were defined in the slot configuration file.")

        slots: list[ParkingSlot] = []

        for index, raw_slot in enumerate(raw_slots, start=1):
            try:
                slot = ParkingSlot(
                    id=str(raw_slot.get("id", index)),
                    x=int(raw_slot["x"]),
                    y=int(raw_slot["y"]),
                    width=int(raw_slot["width"]),
                    height=int(raw_slot["height"]),
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise SlotConfigError(
                    f"Invalid slot definition at index {index}: {raw_slot}"
                ) from exc

            if slot.width <= 0 or slot.height <= 0:
                raise SlotConfigError(
                    f"Slot {slot.id} must have positive width and height values."
                )

            slots.append(slot)

        return slots

    def evaluate_slots(
        self, detections: Iterable[Detection]
    ) -> tuple[list[SlotEvaluation], OccupancyCounts]:
        slots = self.load_slots()
        evaluations: list[SlotEvaluation] = []
        occupied_slots = 0

        for slot in slots:
            max_overlap = 0.0

            for detection in detections:
                overlap = self._calculate_overlap(slot, detection)
                if overlap > max_overlap:
                    max_overlap = overlap

            is_occupied = max_overlap >= self.occupancy_threshold
            if is_occupied:
                occupied_slots += 1

            evaluations.append(
                SlotEvaluation(slot=slot, occupied=is_occupied, overlap=round(max_overlap, 4))
            )

        total_slots = len(slots)
        counts = OccupancyCounts(
            total_slots=total_slots,
            occupied_slots=occupied_slots,
            free_slots=total_slots - occupied_slots,
        )

        return evaluations, counts

    @staticmethod
    def _calculate_overlap(slot: ParkingSlot, detection: Detection) -> float:
        slot_x1, slot_y1, slot_x2, slot_y2 = slot.bounds

        inter_x1 = max(slot_x1, detection.x1)
        inter_y1 = max(slot_y1, detection.y1)
        inter_x2 = min(slot_x2, detection.x2)
        inter_y2 = min(slot_y2, detection.y2)

        if inter_x1 >= inter_x2 or inter_y1 >= inter_y2:
            return 0.0

        intersection_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        return intersection_area / slot.area
