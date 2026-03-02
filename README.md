# Forest Fire Tracking Web Product (Video Wildfire Analysis Web App)

This project is a Flask + Socket.IO web product for **frame-by-frame analysis and visualization** of wildfire videos (fire and smoke). It supports two processing pipelines:

1) **Stable Camera Analysis**: fuses classical pixel segmentation with YOLO-OBB detection to estimate fire area, track fire spread direction, and infer smoke/wind direction via optical flow.  
2) **YOLO Detection View**: a lightweight pipeline that runs YOLO-OBB inference and overlays oriented bounding boxes (OBB) for visualization.

---
