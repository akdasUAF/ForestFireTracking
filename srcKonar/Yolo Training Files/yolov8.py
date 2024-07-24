import wandb
import os
from ultralytics import YOLO

# Load a COCO-pretrained YOLOv5n model
model = YOLO("yolov8n.pt")

# Display model information (optional)
model.info()


results = model.train(data="/content/data.yaml",
                      epochs=50,
                      imgsz=640,
                      # close_mosaic=3,

                      cache=True,
                      batch=16,
                      workers=os.cpu_count(),
                      single_cls=True,

                      hsv_h=0,
                      hsv_s=0,
                      hsv_v=0,
                      degrees=0,
                      translate=0,
                      scale=0,
                      shear=0,
                      perspective=0,
                      flipud=0,
                      fliplr=0,
                      bgr=0,
                      mosaic=0,
                      mixup=0,
                      copy_paste=0,
                      auto_augment=0,
                      erasing=0,
                      crop_fraction=0,



                      # resume=True,
                      save=True,
                      plots=True,

                      name="Yolo v8",)
