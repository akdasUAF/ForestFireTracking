import os
import cv2
import numpy as np
import base64
from threading import Thread
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, request, jsonify
from fire_flow import fire_pixel_segmentation, fire_flow
from smoke_flow import smoke_pixel_segmentation, smoke_flow
from yolo_detection import run_yolo

app = Flask(__name__)
socketio = SocketIO(app)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

threads = True
size_factor = 3

@socketio.on('stop_processing')
def stop_stream():
    global threads
    threads = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/models')
def models():
    return render_template('models.html')

@app.route('/upload', methods=['POST'])
def handle_upload():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file uploaded'}), 400
    
    global threads
    threads = True
    
    video_file = request.files['video']
    filename = video_file.filename
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    video_file.save(video_path)

    global size_factor
    size_factor = int(request.form.get('sizeFactor'))
    
    is_camera_stable = request.form.get('cameraStable') == 'on'
    run_yolo_detection = request.form.get('runYolo') == 'on'
    
    if is_camera_stable and run_yolo_detection:
        thread1 = Thread(target=process_stable_camera, args=(video_path,))
        thread2 = Thread(target=process_yolo_detection, args=(video_path,))
        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()
        return jsonify({'result': "Video successfully processed"})
    elif is_camera_stable:
        process_stable_camera(video_path)
        return jsonify({'result': "Video successfully processed"})
    elif run_yolo_detection:
        process_yolo_detection(video_path)
        return jsonify({'result': "Video successfully processed"})
    else:
        return jsonify({'error': 'Error processing video'})

def process_stable_camera(video_path):
    global size_factor

    cap = cv2.VideoCapture(video_path)
    _, first_frame = cap.read()
    height, width = first_frame.shape[:2]
    new_width = width // size_factor
    new_height = height // size_factor
    first_frame = cv2.resize(first_frame, (new_width, new_height))
    fire_frame = np.zeros_like(first_frame)
    growth = []
    fireX = []
    fireY = []
    prev = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    wind_dir = []

    while cap.isOpened() and threads:
        ret, frame = cap.read()
        if not ret:
            break
        im = cv2.resize(frame, (new_width, new_height))

        fire_mask = fire_pixel_segmentation(im)
        area, fire_frame, contour_im = fire_flow(im, fire_mask, fire_frame, fireX, fireY)
        growth.append(area)

        smoke_mask = smoke_pixel_segmentation(im)
        curr, smoke_frame = smoke_flow(im, prev, smoke_mask, wind_dir)
        prev = curr

        f_mask = cv2.cvtColor(fire_mask, cv2.COLOR_GRAY2BGR)
        s_mask = cv2.cvtColor(smoke_mask, cv2.COLOR_GRAY2BGR)

        row1 = np.hstack((im, f_mask))  
        row2 = np.hstack((contour_im, fire_frame))
        row3 = np.hstack((s_mask, smoke_frame))

        final_frame = np.vstack((row1, row2, row3))
        # print(final_frame.shape)

        _, buffer = cv2.imencode('.jpg', final_frame)
        img_str = base64.b64encode(buffer).decode('utf-8')

        socketio.emit('stable_update', img_str)

        if cv2.waitKey(1) & 0xFF == 27:
            break
    cap.release()

def process_yolo_detection(video_path):
    global size_factor

    cap = cv2.VideoCapture(video_path)
    _, first_frame = cap.read()
    height, width = first_frame.shape[:2]
    new_width = width // size_factor
    new_height = height // size_factor


    while cap.isOpened() and threads:
        ret, frame = cap.read()
        if not ret:
            break

        im = cv2.resize(frame, (new_width, new_height))

        yolo_frame = run_yolo(im)

        _, buffer = cv2.imencode('.jpg', yolo_frame)
        img_str = base64.b64encode(buffer).decode('utf-8')

        socketio.emit('yolo_update', img_str)

        if cv2.waitKey(1) & 0xFF == 27:
            break
    cap.release()

if __name__ == '__main__':
    socketio.run(app, debug=True)
