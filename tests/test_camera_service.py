from __future__ import annotations

import unittest
from unittest.mock import patch

import cv2
import numpy as np

from app.services.camera_service import CameraService


class FakeHeaders(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class FakeHttpResponse:
    def __init__(self, payload: bytes, content_type: str = "multipart/x-mixed-replace") -> None:
        self.payload = payload
        self.offset = 0
        self.headers = FakeHeaders({"Content-Type": content_type})

    def read(self, size: int = -1) -> bytes:
        if size == -1:
            size = len(self.payload) - self.offset

        if self.offset >= len(self.payload):
            return b""

        chunk = self.payload[self.offset : self.offset + size]
        self.offset += len(chunk)
        return chunk

    def __enter__(self) -> "FakeHttpResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class CameraServiceTests(unittest.TestCase):
    def test_extract_jpeg_bytes_returns_first_jpeg(self) -> None:
        image = np.full((8, 8, 3), 180, dtype=np.uint8)
        success, encoded = cv2.imencode(".jpg", image)
        self.assertTrue(success)

        buffer = bytearray(b"header-data" + encoded.tobytes() + b"tail-data")
        jpeg = CameraService._extract_jpeg_bytes(buffer)

        self.assertIsNotNone(jpeg)
        self.assertTrue(jpeg.startswith(b"\xff\xd8"))
        self.assertTrue(jpeg.endswith(b"\xff\xd9"))

    def test_capture_http_frame_reads_mjpeg_stream(self) -> None:
        image = np.full((12, 12, 3), 220, dtype=np.uint8)
        success, encoded = cv2.imencode(".jpg", image)
        self.assertTrue(success)

        payload = (
            b"--dcmjpeg\r\nContent-Type: image/jpeg\r\n\r\n"
            + encoded.tobytes()
            + b"\r\n--dcmjpeg\r\n"
        )
        service = CameraService()

        with patch("app.services.camera_service.urllib.request.urlopen", return_value=FakeHttpResponse(payload)):
            frame = service._capture_http_frame("http://camera/video")

        self.assertEqual(frame.shape[:2], (12, 12))

    def test_capture_http_frame_reports_droidcam_busy_message(self) -> None:
        service = CameraService()
        busy_page = b"<html><body><h5>DroidCam is Busy</h5></body></html>"

        with patch(
            "app.services.camera_service.urllib.request.urlopen",
            return_value=FakeHttpResponse(busy_page, content_type="text/html; charset=UTF-8"),
        ):
            with self.assertRaises(RuntimeError) as context:
                service._capture_http_frame("http://camera/video")

        self.assertIn("DroidCam reports the camera is busy", str(context.exception))


if __name__ == "__main__":
    unittest.main()
