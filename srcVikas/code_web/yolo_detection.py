import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
import torch

global_model = None

def load_model():
    global global_model
    if global_model is None:
        global_model = YOLO('../models/yoloSmall.pt')
        
        if torch.cuda.is_available():
            global_model.to('cuda')

    return global_model

def run_yolo(frame):
    global global_model
    
    if global_model is None:
        global_model = load_model()
        if torch.cuda.is_available():
            global_model.to('cuda')
    
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    # Run inference
    results = global_model.predict(image)
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

def run_yolo_fire_mask(frame):
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    results = global_model.predict(image)
    detections = results[0].obb.xywhr.cpu().numpy()

    mask = np.zeros(frame.shape[:2], dtype=np.uint8)

    for x, y, w, h, r in detections:
        rect = ((x, y), (w, h), np.degrees(r))
        box = cv2.boxPoints(rect)
        box = np.intp(box)
        cv2.fillPoly(mask, [box], 255)

    kernel = np.ones((3,3), np.uint8)
    return cv2.dilate(mask, kernel, iterations=1)