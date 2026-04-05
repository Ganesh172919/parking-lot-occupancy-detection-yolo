# Smart Parking Detection

A minimal parking occupancy project that captures a single frame from an RTSP/HTTP camera URL, detects cars with YOLO, checks overlap against fixed parking slot boxes, and returns slot counts plus an annotated parking image through a simple web interface.

## Features

- Camera input uses only an RTSP or HTTP video stream URL.
- YOLO-based car detection on a single captured frame.
- Fixed parking slots loaded from a JSON file.
- Per-slot occupancy based on detection overlap.
- FastAPI backend with clean service separation.
- Plain HTML/CSS/JavaScript frontend with an on-demand `Show Parking Area` action.

## Project Structure

```text
app/
  config/parking_slots.json
  core/settings.py
  models/
    domain.py
    schemas.py
  services/
    camera_service.py
    detection_service.py
    parking_service.py
    visualization_service.py
  static/
    index.html
    styles.css
    app.js
  main.py
run.py
requirements.txt
tests/test_parking_service.py
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
python run.py
```

4. Open `http://localhost:8000`

FastAPI docs are available at `http://localhost:8000/docs`.

## Configure Parking Slots

Edit `app/config/parking_slots.json` and replace the sample rectangles with your real parking slot coordinates from the camera view:

```json
{
  "slots": [
    { "id": "A1", "x": 40, "y": 120, "width": 140, "height": 90 }
  ]
}
```

Each slot uses:

- `id`: label shown in the UI and on the image
- `x`, `y`: top-left corner
- `width`, `height`: slot size in pixels

## How It Works

1. The frontend sends the camera URL to `POST /api/analyze`.
2. The backend opens the stream and captures one frame.
3. YOLO detects cars in that frame.
4. Each configured parking slot is marked `OCCUPIED` when the car/slot overlap exceeds the threshold.
5. The response returns:

- total slots
- occupied slots
- free slots
- slot-by-slot status
- annotated image as base64

## Notes

- The first analysis request may take longer because the YOLO weights can download automatically the first time.
- The default model is `yolov8n.pt`.
- The default occupancy threshold is `0.20` of slot area overlap.
- By default the detector looks for COCO class `2` (`car`). You can change this with the `TARGET_CLASS_IDS` environment variable if you want to include more vehicle classes.

## Optional Environment Variables

```bash
YOLO_MODEL=yolov8n.pt
DETECTION_CONFIDENCE=0.25
SLOT_OCCUPANCY_THRESHOLD=0.20
CAMERA_READ_ATTEMPTS=12
CAMERA_WARMUP_FRAMES=5
TARGET_CLASS_IDS=2
```

## Run the Tests

```bash
python -m unittest discover -s tests
```
