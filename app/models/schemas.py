from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    camera_url: str = Field(..., description="RTSP/HTTP camera stream URL")


class SlotStatus(BaseModel):
    id: str
    x: int
    y: int
    width: int
    height: int
    state: Literal["FREE", "OCCUPIED"]
    overlap: float


class ParkingCountsResponse(BaseModel):
    total_slots: int
    occupied_slots: int
    free_slots: int


class AnalyzeResponse(BaseModel):
    counts: ParkingCountsResponse
    slot_statuses: list[SlotStatus]
    annotated_image: str = Field(..., description="Base64 encoded JPEG image")
