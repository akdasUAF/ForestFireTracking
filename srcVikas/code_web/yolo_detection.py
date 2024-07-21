import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO

model = YOLO('../models/yoloNano.pt')

def run_yolo(frame):
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    results = model.predict(image)
    detections = results[0].obb.xywhr.cpu().numpy()

    noOfDetections = len(detections)

    for i in range(noOfDetections):
        x, y, w, h, r = detections[i]

        rect = ((x, y), (w, h), np.degrees(r))
        box = cv2.boxPoints(rect)
        box = np.intp(box)

        cv2.polylines(frame, [box], True, (0,0,255), 3)
    
    cv2.putText(frame, str(noOfDetections), (100,100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,255), 4, cv2.LINE_AA)

    return frame

        
