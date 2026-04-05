from __future__ import annotations

import time
import urllib.request

import cv2
import numpy as np


class CameraService:
    def __init__(self, read_attempts: int = 12, warmup_frames: int = 5) -> None:
        self.read_attempts = read_attempts
        self.warmup_frames = warmup_frames

    @staticmethod
    def validate_camera_url(camera_url: str) -> None:
        if not camera_url or not camera_url.lower().startswith(
            ("rtsp://", "http://", "https://")
        ):
            raise ValueError("Camera URL must start with rtsp://, http://, or https://")

    def capture_frame(self, camera_url: str) -> np.ndarray:
        self.validate_camera_url(camera_url)

        try:
            return self._capture_frame_with_opencv(camera_url)
        except RuntimeError as opencv_error:
            if camera_url.lower().startswith(("http://", "https://")):
                try:
                    return self._capture_http_frame(camera_url)
                except RuntimeError as http_error:
                    raise RuntimeError(
                        "Unable to capture a frame from the provided camera URL. "
                        f"OpenCV error: {opencv_error}. HTTP fallback error: {http_error}"
                    ) from http_error

            raise opencv_error

    def _capture_frame_with_opencv(self, camera_url: str) -> np.ndarray:
        capture = self._open_capture(camera_url)
        frame: np.ndarray | None = None
        successful_reads = 0

        try:
            capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            for _ in range(self.read_attempts):
                ok, candidate = capture.read()

                if ok and candidate is not None and candidate.size > 0:
                    frame = candidate
                    successful_reads += 1
                    if successful_reads >= self.warmup_frames:
                        break
                else:
                    time.sleep(0.1)
        finally:
            capture.release()

        if frame is None:
            raise RuntimeError("Unable to capture a frame from the stream with OpenCV.")

        return frame

    def _capture_http_frame(self, camera_url: str) -> np.ndarray:
        request = urllib.request.Request(
            camera_url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*",
                "Connection": "close",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                content_type = (response.headers.get("Content-Type") or "").lower()
                if "text/html" in content_type:
                    page = response.read(4096).decode("utf-8", errors="ignore").lower()
                    if "droidcam is busy" in page:
                        raise RuntimeError(
                            "DroidCam reports the camera is busy. Close any browser tab or app "
                            f"already using {camera_url} and try again."
                        )
                    if "video inactive" in page:
                        raise RuntimeError(
                            "DroidCam reports video is inactive. Start the camera stream in the "
                            "DroidCam app and try again."
                        )
                    raise RuntimeError(
                        "The camera URL returned an HTML page instead of an image/video frame."
                    )

                buffer = bytearray()
                deadline = time.monotonic() + 15

                while time.monotonic() < deadline:
                    chunk = response.read(4096)
                    if not chunk:
                        break

                    buffer.extend(chunk)
                    jpeg_bytes = self._extract_jpeg_bytes(buffer)
                    if jpeg_bytes is not None:
                        frame = cv2.imdecode(
                            np.frombuffer(jpeg_bytes, dtype=np.uint8),
                            cv2.IMREAD_COLOR,
                        )
                        if frame is None or frame.size == 0:
                            raise RuntimeError("Received an HTTP image frame, but decoding failed.")
                        return frame

                    if len(buffer) > 8_000_000:
                        del buffer[:-1_000_000]
        except Exception as exc:
            raise RuntimeError(f"Unable to read a frame from the HTTP camera stream: {exc}") from exc

        raise RuntimeError("No decodable JPEG frame was found in the HTTP camera stream.")

    @staticmethod
    def _extract_jpeg_bytes(buffer: bytearray) -> bytes | None:
        start = buffer.find(b"\xff\xd8")
        if start == -1:
            return None

        end = buffer.find(b"\xff\xd9", start + 2)
        if end == -1:
            return None

        jpeg_bytes = bytes(buffer[start : end + 2])
        del buffer[: end + 2]
        return jpeg_bytes

    @staticmethod
    def _open_capture(camera_url: str) -> cv2.VideoCapture:
        preferred_capture = cv2.VideoCapture(camera_url, cv2.CAP_FFMPEG)
        if preferred_capture.isOpened():
            return preferred_capture

        preferred_capture.release()
        fallback_capture = cv2.VideoCapture(camera_url)

        if not fallback_capture.isOpened():
            fallback_capture.release()
            raise RuntimeError("Unable to open the camera stream.")

        return fallback_capture
