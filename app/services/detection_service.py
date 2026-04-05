from __future__ import annotations

from collections.abc import Iterable

import numpy as np
from ultralytics import YOLO

from app.models.domain import Detection


class DetectionService:
    def __init__(
        self,
        model_name: str,
        confidence_threshold: float,
        target_class_ids: Iterable[int],
    ) -> None:
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.target_class_ids = tuple(sorted(set(target_class_ids)))
        self._model: YOLO | None = None

    def detect(self, frame: np.ndarray) -> list[Detection]:
        model = self._get_model()
        results = model.predict(
            source=frame,
            conf=self.confidence_threshold,
            classes=list(self.target_class_ids),
            verbose=False,
        )

        detections: list[Detection] = []

        for result in results:
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                continue

            names = self._normalize_names(result.names)
            coordinates = boxes.xyxy.cpu().tolist()
            confidences = boxes.conf.cpu().tolist()
            class_ids = boxes.cls.cpu().tolist()

            for coords, confidence, class_id in zip(coordinates, confidences, class_ids):
                x1, y1, x2, y2 = [int(round(value)) for value in coords]
                numeric_class_id = int(class_id)
                detections.append(
                    Detection(
                        x1=x1,
                        y1=y1,
                        x2=x2,
                        y2=y2,
                        confidence=float(confidence),
                        class_id=numeric_class_id,
                        label=names.get(numeric_class_id, "car"),
                    )
                )

        return detections

    def _get_model(self) -> YOLO:
        if self._model is None:
            self._model = YOLO(self.model_name)
        return self._model

    @staticmethod
    def _normalize_names(names: list[str] | dict[int, str]) -> dict[int, str]:
        if isinstance(names, dict):
            return names
        return {index: label for index, label in enumerate(names)}

