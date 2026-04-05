from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from app.models.domain import Detection
from app.services.parking_service import ParkingService


class ParkingServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.slot_config_path = Path(self.temp_dir.name) / "parking_slots.json"
        self.slot_config_path.write_text(
            json.dumps(
                {
                    "slots": [
                        {"id": "S1", "x": 0, "y": 0, "width": 100, "height": 100},
                        {"id": "S2", "x": 120, "y": 0, "width": 100, "height": 100}
                    ]
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_evaluate_slots_marks_expected_slot_as_occupied(self) -> None:
        service = ParkingService(self.slot_config_path, occupancy_threshold=0.2)
        detections = [
            Detection(
                x1=5,
                y1=5,
                x2=95,
                y2=95,
                confidence=0.92,
                class_id=2,
                label="car",
            )
        ]

        evaluations, counts = service.evaluate_slots(detections)

        self.assertEqual(counts.total_slots, 2)
        self.assertEqual(counts.occupied_slots, 1)
        self.assertEqual(counts.free_slots, 1)
        self.assertTrue(evaluations[0].occupied)
        self.assertFalse(evaluations[1].occupied)

    def test_evaluate_slots_marks_all_slots_free_with_no_overlap(self) -> None:
        service = ParkingService(self.slot_config_path, occupancy_threshold=0.2)
        detections = [
            Detection(
                x1=260,
                y1=20,
                x2=320,
                y2=80,
                confidence=0.88,
                class_id=2,
                label="car",
            )
        ]

        evaluations, counts = service.evaluate_slots(detections)

        self.assertEqual(counts.total_slots, 2)
        self.assertEqual(counts.occupied_slots, 0)
        self.assertEqual(counts.free_slots, 2)
        self.assertFalse(evaluations[0].occupied)
        self.assertFalse(evaluations[1].occupied)


if __name__ == "__main__":
    unittest.main()

