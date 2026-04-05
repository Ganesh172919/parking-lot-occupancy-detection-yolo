from __future__ import annotations

import base64

import cv2
import numpy as np

from app.models.domain import Detection, OccupancyCounts, SlotEvaluation


class VisualizationService:
    FREE_COLOR = (34, 163, 76)
    OCCUPIED_COLOR = (30, 30, 220)
    DETECTION_COLOR = (23, 179, 255)
    TEXT_COLOR = (255, 255, 255)
    PANEL_COLOR = (24, 32, 48)

    def annotate(
        self,
        frame: np.ndarray,
        evaluations: list[SlotEvaluation],
        detections: list[Detection],
        counts: OccupancyCounts,
    ) -> np.ndarray:
        annotated = frame.copy()
        self._draw_summary_panel(annotated, counts)
        self._draw_detections(annotated, detections)
        self._draw_slots(annotated, evaluations)
        return annotated

    @staticmethod
    def encode_base64(frame: np.ndarray) -> str:
        success, encoded_image = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 90],
        )

        if not success:
            raise RuntimeError("Unable to encode the annotated image.")

        return base64.b64encode(encoded_image.tobytes()).decode("ascii")

    def _draw_summary_panel(self, image: np.ndarray, counts: OccupancyCounts) -> None:
        cv2.rectangle(image, (10, 10), (320, 95), self.PANEL_COLOR, thickness=-1)
        cv2.putText(
            image,
            "Parking Summary",
            (24, 38),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            self.TEXT_COLOR,
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            image,
            f"Total: {counts.total_slots}",
            (24, 62),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.TEXT_COLOR,
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            image,
            f"Occupied: {counts.occupied_slots}  Free: {counts.free_slots}",
            (24, 86),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.TEXT_COLOR,
            2,
            cv2.LINE_AA,
        )

    def _draw_detections(self, image: np.ndarray, detections: list[Detection]) -> None:
        for detection in detections:
            cv2.rectangle(
                image,
                (detection.x1, detection.y1),
                (detection.x2, detection.y2),
                self.DETECTION_COLOR,
                2,
            )

            label = f"{detection.label} {detection.confidence:.2f}"
            cv2.putText(
                image,
                label,
                (detection.x1, max(20, detection.y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                self.DETECTION_COLOR,
                2,
                cv2.LINE_AA,
            )

    def _draw_slots(self, image: np.ndarray, evaluations: list[SlotEvaluation]) -> None:
        for evaluation in evaluations:
            slot = evaluation.slot
            color = self.OCCUPIED_COLOR if evaluation.occupied else self.FREE_COLOR
            state = "OCCUPIED" if evaluation.occupied else "FREE"

            cv2.rectangle(
                image,
                (slot.x, slot.y),
                (slot.x + slot.width, slot.y + slot.height),
                color,
                3,
            )

            label = f"{slot.id}: {state}"
            cv2.putText(
                image,
                label,
                (slot.x + 4, max(20, slot.y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
                cv2.LINE_AA,
            )

