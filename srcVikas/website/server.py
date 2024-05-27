from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import cv2
import torch
# from PIL import Image
from ultralytics import YOLO
import numpy as np
from flask_socketio import SocketIO, emit
from threading import Thread
import base64
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

app = Flask(__name__)
socketio = SocketIO(app)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

threads = [True, True]

# model = torch.hub.load('ultralytics/yolov5', 'custom', path='../models/yoloFire.pt')

# Load the YOLOv8 model
model = YOLO('../models/yoloNano.pt', verbose=False)

def yolo(im, yolo_frame, size=640):
    # g = size / max(im.size)
    # im = im.resize((int(x * g) for x in im.size), Image.LANCZOS)
    results = model(im)
    detections = results[0].obb.xywhr.cpu().numpy()

    # result_image = Image.fromarray(results.ims[0])
    # result_frame = np.array(result_image)

    # for box in results.xyxy[0]:
    #     xmin, ymin, xmax, ymax, _, _ = box
    #     cv2.rectangle(result_frame, (int(xmin), int(ymin)), (int(xmax), int(ymax)), (255, 0, 0), 2)
    #     cv2.rectangle(yolo_frame, (int(xmin), int(ymin)), (int(xmax), int(ymax)), (0, 0, 255), -1)

    for i in range(len(detections)):
            x, y, w, h, r = detections[i]
#             score = scores[i]
#             class_idx = int(classes[i])

            # Convert the center (x, y), width, height, and rotation angle into a box format
            rect = ((x, y), (w, h), np.degrees(r))
            box = cv2.boxPoints(rect)
            box = np.intp(box)

            # Draw the bounding box
#             color = colors[class_idx % len(colors)]
#             label = f"{labels[class_idx % len(labels)]}: {score:.2f}"
            cv2.polylines(im, [box], True, (0,0,255), 2)
            cv2.fillPoly(yolo_frame, [box.reshape((-1, 1, 2))], (0, 0, 255))
#             cv2.putText(frame, label, (int(box[0][0]), int(box[0][1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    area = 0
    gray = cv2.cvtColor(yolo_frame, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        area += cv2.contourArea(contour)

    return im, yolo_frame, results, area

def motion(motion_frame, prvs, new):
    flow = cv2.calcOpticalFlowFarneback(prvs, new, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    for y in range(0, motion_frame.shape[0], 10):
        for x in range(0, motion_frame.shape[1], 10):
            fx, fy = flow[y, x]
            cv2.line(motion_frame, (x, y), (int(x + fx), int(y + fy)), [0, 0, 255], 1)
    return flow, motion_frame

@socketio.on('stop_stream')
def stop_stream():
    print("Stopping stream")
    threads[0] = False
    threads[1] = False
        
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        process_thread = Thread(target=process_video, args=(file_path,))
        process_thread.start()

        return jsonify({'result': "Video successfully processed"})
    else:
        return jsonify({'error': 'Error uploading video'})

def process_video(file_path):
    yolo_cap = cv2.VideoCapture(file_path)
    motion_cap = cv2.VideoCapture(file_path)

    fps = yolo_cap.get(cv2.CAP_PROP_FPS)

    ## yolo variables
    _, old_frame = motion_cap.read()
    yolo_area_frame = np.zeros_like(old_frame)
    old_area = 0
    areas = []
    area_growth = []

    ## motion varibales ##
    motion_frame = np.zeros_like(old_frame)
    prvs = cv2.cvtColor(old_frame, cv2.COLOR_BGR2GRAY)
    avgx = []
    avgy = []
    angles = []
    speed = []

    def run_yolo():
        nonlocal old_area, yolo_area_frame
        while yolo_cap.isOpened() and threads[0]:
            ret, frame = yolo_cap.read()
            if not ret:
                break

            # frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            yolo_result_frame, yolo_frame, yolo_results, new_area = yolo(frame, yolo_area_frame)
            areas.append(new_area)
            area_growth.append(new_area - old_area)
            old_area = new_area

            _, buffer = cv2.imencode('.jpg', yolo_result_frame)
            img_str = base64.b64encode(buffer).decode('utf-8')
            # print("Emitting yolo frame")

            socketio.emit("yolo_frame", img_str)

    def run_motion():
        nonlocal prvs, motion_frame
        while motion_cap.isOpened() and threads[1]:
            ret, new_frame = motion_cap.read()
            if not ret:
                break

            new = cv2.cvtColor(new_frame, cv2.COLOR_BGR2GRAY)
            flow, motion_frame = motion(motion_frame, prvs, new)
            prvs = new

            avgx.append(np.mean(flow[..., 0]))
            avgy.append(np.mean(flow[..., 1]))


            if len(avgx) > 30: 
                avg_fx = np.mean(avgx)
                avg_fy = np.mean(avgy)
                avg_direction_angle = np.arctan2(avg_fy, avg_fx)
                avg_direction_degrees = np.degrees(avg_direction_angle)
                
                avg_speed = np.sqrt(avg_fx**2 + avg_fy**2)
                
                speed.append(avg_speed)
                
                angles.append(avg_direction_degrees)

                avgx.pop()
                avgy.pop()

            _, buffer = cv2.imencode('.jpg', motion_frame)
            img_str = base64.b64encode(buffer).decode('utf-8')
            # print('Emitting motion frame')
            socketio.emit('motion_frame', img_str)

    yolo_thread = Thread(target=run_yolo)
    motion_thread = Thread(target=run_motion)

    threads[0] = True
    threads[1] = True

    yolo_thread.start()
    motion_thread.start()

    yolo_thread.join()
    motion_thread.join()

    # Scaling the variables
    # area_scaler = MinMaxScaler()
    # areas_normalized = area_scaler.fit_transform(np.array(areas).reshape(-1, 1)).flatten()

    # growth_scaler = MinMaxScaler()
    # area_growth_normalized = growth_scaler.fit_transform(np.array(area_growth).reshape(-1, 1)).flatten()

    # speed_scaler = MinMaxScaler()
    # speed_normalized = speed_scaler.fit_transform(np.array(speed).reshape(-1, 1)).flatten()

    yolo_frame_numbers = np.arange(len(areas))  # Assuming areas, area_growth, speed all have the same length
    yolo_time_seconds = yolo_frame_numbers / fps

    motion_frame_numbers = np.arange(len(angles))  # Assuming areas, area_growth, speed all have the same length
    motion_time_seconds = motion_frame_numbers / fps

    # Plotting
    plt.figure(figsize=(15, 11))

    # Plot for areas
    plt.subplot(2, 2, 1)
    sns.lineplot(x=yolo_time_seconds, y=areas, color='b', linewidth=1)
    plt.ylabel('Area (pixels)', fontsize=12)
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.title(f'Area (Min: {min(areas):.2f}, Max: {max(areas):.2f}, Mean: {np.mean(areas):.2f}, Dev: {np.std(areas):.2f})')

    # Plot for area growth
    plt.subplot(2, 2, 3)
    sns.lineplot(x=yolo_time_seconds, y=area_growth, color='r', linewidth=1)
    plt.ylabel('Growth (pixels)', fontsize=12)
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.title(f'Growth (Min: {min(area_growth):.2f}, Max: {max(area_growth):.2f}, Mean: {np.mean(area_growth):.2f}, Dev: {np.std(area_growth):.2f})')

    # Plot for speed
    plt.subplot(2, 2, 2)
    sns.lineplot(x=motion_time_seconds, y=speed, color='g', linewidth=1)
    plt.ylabel('Speed (pixels)', fontsize=12)
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.title(f'Speed (Min: {min(speed):.2f}, Max: {max(speed):.2f}, Mean: {np.mean(speed):.2f}, Dev: {np.std(speed):.2f})')

    # Plotting polar plot in the second column
    plt.subplot(2, 2, 4, polar=True)
    plt.hist(np.radians(angles), bins=30, color='skyblue', alpha=0.7)
    plt.xlabel('Direction', fontsize=12)
    plt.gca().set_theta_direction(-1)
    plt.gca().set_rticks([])
    plt.title('Direction')

    # Optionally, adjust the spacing between subplots
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.4, wspace=0.4)

    plt.savefig(os.path.join(app.config['UPLOAD_FOLDER'], 'metrics.png'))
    socketio.emit('metrics')

    # motion_cap.release()
    # yolo_cap.release()

    return "Videomotion"

if __name__ == '__main__':
    socketio.run(app, debug=True)
