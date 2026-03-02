# Forest Fire and Smoke Research (Video Wildfire Analysis Web App)

The product is openly accessible at http://137.229.25.190:5000/, the entry gate is "Wildfire Management System".

This project is a Flask + Socket.IO web product for **frame-by-frame analysis and visualization** of wildfire videos (fire and smoke). It supports two processing pipelines:

1) **Stable Camera Analysis**: fuses classical pixel segmentation with YOLO-OBB detection to estimate fire area, track fire spread direction, and infer smoke/wind direction via optical flow.  
2) **YOLO Detection View**: a lightweight pipeline that runs YOLO-OBB inference and overlays oriented bounding boxes (OBB) for visualization.

---
## End-to-End Workflow (Upload → Processing → Outputs)

### 1. Video Upload & Parameter Setup
On the `/upload` page, users upload a video and configure key parameters (e.g., resize factor, sliding-window sizes, whether to enable stable-camera analysis, whether to enable YOLO detection, etc.).

To convert pixel area into real-world area (m²), the system reads drone/camera metadata (e.g., **sensor width** and **focal length**) or uses user-provided camera parameters, and combines them with `objectDistance` (distance to target) to estimate ground sampling distance (GSD).

---
### 2. Two Pipelines (Either can run alone, or both can run together)

## A. Stable Camera Analysis Pipeline (`process_stable_camera`)
This pipeline processes the video frame-by-frame:

### A1) Preprocessing & Resizing
- Read frames and resize by `size_factor` to reduce compute and stabilize throughput.

### A2) Fire Region Extraction: Pixel Segmentation + YOLO-OBB Fusion
The fire mask is built by combining two sources:

- **Classical fire pixel segmentation** (`fire_pixel_segmentation()`): applies a set of heuristic rules in YCrCb and RGB spaces (channel thresholds and relationships) to extract candidate fire pixels, followed by morphological cleanup.
- **YOLO-OBB fire mask** (`run_yolo_fire_mask()`): runs OBB detection and fills each detected OBB polygon to create a binary fire mask.
- **Fusion strategy**: the two masks are blended using a weight `alpha`, then thresholded into a final, more robust binary fire mask. This typically improves robustness by combining deep model localization with traditional segmentation detail.

### A3) Fire Area Estimation & Spread Trajectory (`fire_flow`)
- Extract contours from the fire mask and compute the fire **pixel area** per frame.
- Convert pixel area to **real-world area (m²)** using GSD (computed from sensor width, focal length, object distance, and image width).
- Track centroid motion of the fire region over time; apply a sliding window (`mFrames`) to smooth the direction estimate and draw a spread-direction arrow. The pipeline outputs an estimated spread direction angle.

### A4) Smoke / Wind Direction Estimation (`smoke_flow`)
- Generate a smoke mask with `smoke_pixel_segmentation()` using HSV-based thresholding (plus inversion and morphology to isolate smoke candidates).
- Estimate motion with Farneback optical flow (`cv2.calcOpticalFlowFarneback`) in the smoke region, and draw local flow arrows.
- Aggregate flow directions into a per-frame “smoke/wind direction angle,” then smooth with a sliding window (`nFrames`) for a stable directional estimate.

### A5) Real-Time Visualization Output (Socket.IO)
Each frame is assembled into a 2×2 panel (e.g., original frame / fire mask / smoke mask / overlay visualization), JPEG-encoded and Base64-packed, then pushed to the frontend via the `stable_update` Socket.IO event.

### A6) Post-Run Analytics Plots
After processing finishes, the system aggregates and produces summary figures:
- Fire area (m²) over time
- Fire area growth rate over time
- Polar distribution of smoke/wind directions
- Fire spread path (trajectory of centroid points)

These plots are produced by `analysis.py::graph()`, encoded as Base64 PNG, and sent to the frontend via the `analysis` event.

---

## B. YOLO Detection Pipeline (`process_yolo_detection`)
This pipeline is optimized for “detection-only” visualization:

### B1) Frame-by-Frame YOLO-OBB Inference (`run_yolo`)
- Run YOLO-OBB on each frame, read `results[0].obb.xywhr` (center x/y, width, height, rotation),
- Convert each OBB to a polygon and draw it on the frame,
- Overlay the number of detections.

### B2) Real-Time Streaming to Frontend
Processed frames are JPEG-encoded + Base64 and emitted to the frontend via the `yolo_update` Socket.IO event.

---

## Project Structure (Mapped to the Workflow)
- `app.py`: web routes, video upload, thread orchestration, Socket.IO streaming (main entrypoint)
- `yolo_detection.py`: YOLO-OBB model loading and inference; supports OBB overlay and OBB-derived binary masks
- `fire_flow.py`: fire pixel segmentation, real-world area estimation, and fire spread tracking
- `smoke_flow.py`: smoke segmentation and optical-flow-based direction estimation
- `analysis.py`: aggregated analytics plots (area trends, growth rate, direction distribution, spread path)
- `templates/index.html` etc.: frontend pages (upload, model, team pages, and visualization UI)

---

## Outputs
- **Real-time visualizations**: original frames, fire/smoke masks, overlay views, YOLO OBB detections
- **Quantitative analysis**:
  - Fire area (m²) over time
  - Fire area growth rate
  - Smoke/wind direction distribution
  - Fire spread path and direction angle estimates

---

## Quick Start (Example)
- Run `app.py`, then visit `/` and navigate to `/upload` to submit a video for analysis.
- Socket.IO streams frames and analytics plots to the frontend in real time.

---

## Notes (Engineering Considerations)
- The stable-camera pipeline assumes limited camera motion. If the camera shakes strongly, consider video stabilization or camera-motion compensation; otherwise, optical flow and trajectory estimates can be degraded.
- If stable analysis and YOLO detection run concurrently, ensure YOLO inference is thread-safe (e.g., use an inference lock or one model instance per thread) to avoid concurrency issues during initialization/fusion.
