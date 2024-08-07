import subprocess
import time
import csv
import cv2
import sys
import os
from ultralytics import YOLO

def parse_tegrastats(log_file):
    # Parse the tegrastats log file to estimate power consumption
    with open(log_file, 'r') as f:
        lines = f.readlines()

    # Calculate average utilization:
    # Parse each line to extract CPU and GPU utilization, then calculate power
    cpu_utilization = []
    gpu_utilization = []

    for line in lines:
        parts = line.split()
        for part in parts:
            if part.startswith('CPU'):
                try:
                    cpu_util = int(part.split('@')[1].replace('%', ''))
                    cpu_utilization.append(cpu_util)
                except (IndexError, ValueError):
                    # Handle parsing errors gracefully
                    continue
            elif part.startswith('GR3D_FREQ'):
                try:
                    gpu_util = int(part.split('@')[1].replace('%', ''))
                    gpu_utilization.append(gpu_util)
                except (IndexError, ValueError):
                    # Handle parsing errors gracefully
                    continue

    avg_cpu_util = sum(cpu_utilization) / len(cpu_utilization) if cpu_utilization else 0
    avg_gpu_util = sum(gpu_utilization) / len(gpu_utilization) if gpu_utilization else 0

    # Estimate power consumption based on utilization, 5W is the basic consumption
    # /100 means turning percentage into a fraction, * 1 means there should consider 
    # the additional power consumption in watts associated with full utilization (100%)
    # but I really don't know how much this factor should be
    estimated_power = 5 + (avg_cpu_util / 100) * 1 + (avg_gpu_util / 100) * 1
    return estimated_power

# Start tegrastats and save the process
log_file = 'tegrastats_log.txt'
tegrastats_process = subprocess.Popen(['tegrastats', '--interval', '1000', '--logfile', log_file])

start_time = time.time()

try:
    # Load the YOLOv8 model
    #model_name = 'YOLOv5'
    #model = YOLO(r'Fire Detect v3/Yolo_v5/YoloV5.pt')
    #model_name = 'YOLOv8'
    #model = YOLO(r'Fire Detect v3/Yolo_v8/best.pt')
    #model_name = 'YOLOv10'
    #model = YOLO(r'Fire Detect v3/Yolo_v10/best.pt')
    #model_name = 'yoloOBBNV5'
    #model = YOLO(r'Fire Detect V2/yoloOBB_N_V5/yolo OBB N.pt')
    model_name = 'yoloOBBSV0'
    model = YOLO(r'Fire Detect V2/yoloOBB_S_V0/YOLO OBB S.pt')

    # Open the video file
    video_path = "../Videos/1-Zenmuse_X4S_1-00.00.00.000-00.00.40.737.mp4"
    cap = cv2.VideoCapture(video_path)

    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')  # You can also use 'XVID'

    # Output name and codec
    out = cv2.VideoWriter('output.avi', fourcc, fps, (width, height))

    # Loop through the video frames
    while cap.isOpened():
        # Read a frame from the video
        success, frame = cap.read()

        if success:
            # Run YOLOv8 inference on the frame
            results = model(frame)

            # Visualize the results on the frame
            annotated_frame = results[0].plot()

            out.write(annotated_frame)

            # Display the annotated frame
            # cv2.imshow("YOLOv8 Inference", annotated_frame)

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            # Break the loop if the end of the video is reached
            break

    # Release the video capture object and close the display window
    cap.release()
    out.release()
    cv2.destroyAllWindows()

finally:
    # Stop tegrastats once the script finishes
    tegrastats_process.terminate()

end_time = time.time()
running_time = end_time - start_time

# Estimate energy consumption from parsed data
estimated_power = parse_tegrastats(log_file)
estimated_energy = estimated_power * (running_time / 3600)  # in watt-hours

# Write to CSV
#csv_file = 'energy_yolov5_3.csv'
#csv_file = 'energy_yolov8_3.csv'
#csv_file = 'energy_yolov10_3.csv'
#csv_file = 'energy_yoloOBBNV5_3.csv'
csv_file = 'energy_yoloOBBSV0_3.csv'

with open(csv_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Model Name', 'Running Time (s)', 'Estimated Energy (Wh)'])
    writer.writerow([model_name, running_time, estimated_energy])

print("CSV written to %s" % csv_file)

