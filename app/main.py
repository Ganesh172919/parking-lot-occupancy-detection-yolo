from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.settings import Settings
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, ParkingCountsResponse, SlotStatus
from app.services.camera_service import CameraService
from app.services.detection_service import DetectionService
from app.services.parking_service import ParkingService, SlotConfigError
from app.services.visualization_service import VisualizationService

settings = Settings()

camera_service = CameraService(
    read_attempts=settings.camera_read_attempts,
    warmup_frames=settings.camera_warmup_frames,
)
detection_service = DetectionService(
    model_name=settings.model_name,
    confidence_threshold=settings.detection_confidence,
    target_class_ids=settings.target_class_ids,
)
parking_service = ParkingService(
    slot_config_path=settings.slot_config_path,
    occupancy_threshold=settings.occupancy_threshold,
)
visualization_service = VisualizationService()

app = FastAPI(title="Smart Parking Detection", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(settings.static_dir / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "model": settings.model_name,
        "slot_config": str(settings.slot_config_path),
    }


@app.get("/api/slots")
def get_slots() -> dict[str, list[dict[str, int | str]]]:
    try:
        slots = parking_service.load_slots()
    except SlotConfigError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "slots": [
            {
                "id": slot.id,
                "x": slot.x,
                "y": slot.y,
                "width": slot.width,
                "height": slot.height,
            }
            for slot in slots
        ]
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze_parking(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        frame = camera_service.capture_frame(request.camera_url)
        detections = detection_service.detect(frame)
        evaluations, counts = parking_service.evaluate_slots(detections)
        annotated_frame = visualization_service.annotate(frame, evaluations, detections, counts)
        encoded_image = visualization_service.encode_base64(annotated_frame)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (RuntimeError, SlotConfigError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AnalyzeResponse(
        counts=ParkingCountsResponse(
            total_slots=counts.total_slots,
            occupied_slots=counts.occupied_slots,
            free_slots=counts.free_slots,
        ),
        slot_statuses=[
            SlotStatus(
                id=evaluation.slot.id,
                x=evaluation.slot.x,
                y=evaluation.slot.y,
                width=evaluation.slot.width,
                height=evaluation.slot.height,
                state="OCCUPIED" if evaluation.occupied else "FREE",
                overlap=evaluation.overlap,
            )
            for evaluation in evaluations
        ],
        annotated_image=encoded_image,
    )

