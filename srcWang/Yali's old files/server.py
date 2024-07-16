from flask import Flask, request, render_template, jsonify, send_from_directory
import os
import cv2
import torch
from PIL import Image
import numpy as np
from ultralytics import YOLO  # YOLOv8
import tempfile
# import unittest
import logging

app = Flask(__name__)
yolov5_model = torch.hub.load('ultralytics/yolov5', 'custom', '../srcVikas/models/yoloFire.pt')
yolov8_model = YOLO('../srcKonar/Inference V1/Yolo Weights/yoloOBB_N_V5/best.pt')

# YOLOv5 model parameters
pd = 0
text = "emergency"
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.8
font_thickness = 1
text_color = (255, 255, 255)  # White color
pixel_length_meters = 0.05

def yolo(im, size=640):
    # for YOLOv5
    g = (size / max(im.size))  
    im = im.resize((int(x * g) for x in im.size), Image.LANCZOS)
    results = yolov5_model(im)
#     results.render()  
    result_image = Image.fromarray(results.ims[0])
    result_frame = np.array(result_image)
    return results, result_frame


def process_video_yolov5(video_path, output_path):
    # YOLOv5
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    color = [255, 255, 255]
    avgx = []
    avgy = []
    # Clockwise positive direction
    # Open video file
    cap = cv2.VideoCapture(video_path)
    # cap = cv2.VideoCapture('../DemoVideos/paperFire2.mp4')
    # cap.set(cv2.CAP_PROP_POS_FRAMES, 1000)
    # Create random colors for visualizing optical flow tracks
    # color = np.random.randint(0,255,(100,3))
    ret, frame1 = cap.read()
    prvs = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    hsv = np.zeros_like(frame1)
    hsv[...,1] =  255  # Assigning 255 to Saturation Value in hsv Image
    # Create a black frame for motion visualization
    black_frame = np.zeros_like(frame1)
    frame_count = 1
    while True:
        ret, frame2 = cap.read()
    #     frame_count += 1
        if ret and frame_count:
    #         frame_count = 0
            new = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            # Calculate Optical Flow
            flow = cv2.calcOpticalFlowFarneback(prvs, new, None, 
                                                0.5, 3, 15, 3, 5, 1.2, 0)
            # Get average flow direction
            avgx.append(np.mean(flow[..., 0]))
            avgy.append(np.mean(flow[..., 1]))
            if len(avgx) > 30: 
                avg_fx = np.mean(avgx)
                avg_fy = np.mean(avgy)
                avg_direction_angle = np.arctan2(avg_fy, avg_fx)
                avg_direction_degrees = np.degrees(avg_direction_angle)
                # Set text on black_frame
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(frame2, f"Direction wrt X+: {avg_direction_degrees:.2f} degrees", (10, 30), font, 1, (0, 255, 0), 1, cv2.LINE_AA)
                avgx.pop()
                avgy.pop()
            # Overlay motion visualization onto the original frame
            for y in range(0, black_frame.shape[0], 10):
                for x in range(0, black_frame.shape[1], 10):
                    fx, fy = flow[y, x]
                    cv2.line(black_frame, (x, y), (int(x + fx), int(y + fy)), color, 1)
            color[0] -= 1
            color[1] -= 1
            # Display original video and motion visualization
            # cv2.imshow('Original Video', frame2)
            # cv2.imshow('Fire Spread Motion', black_frame)
            out.write(black_frame)
        
            prvs = new
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break   
    # Release video capture object and close all windows
    # cap.release()
    out.release()

def process_video_yolov8(video_path, output_path):
    # YOLOv8
    cap = cv2.VideoCapture(video_path)
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')  # You can also use 'XVID'

    # Output name and codec
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    # Loop through the video frames
    while cap.isOpened():
        # Read a frame from the video
        success, frame = cap.read()

        if success:
            # Run YOLOv8 inference on the frame
            results = yolov8_model(frame)

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
    # cap.release()
    out.release() 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_video():
    try:
        video_file = request.files['video']
        base_path = os.path.join(os.getcwd(), 'videos')
        original_video_path = os.path.join(base_path, video_file.filename)
        # print(original_video_path)

        video_file.save(original_video_path)
        print("Saved the original video at:", original_video_path)  # Debug print

        # Respond with the paths to the processed videos
        response = jsonify({
            "status": "File uploaded successfully",
            "filename": video_file.filename
            # "yolov5": '/videos/' + os.path.basename(yolov5_output_path),
            # "yolov8": '/videos/' + os.path.basename(yolov8_output_path)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')  # Ensure CORS policies are not blocking requests
        return response
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/process_yolov5/<filename>')
def process_yolov5(filename):
    input_path = os.path.join(os.getcwd(), 'videos', filename)
    output_path = os.path.join(os.getcwd(), 'videos', f"yolov5_{filename}")
    process_video_yolov5(input_path, output_path)
    return send_from_directory('videos', f"yolov5_{filename}")

@app.route('/process_yolov8/<filename>')
def process_yolov8(filename):
    input_path = os.path.join(os.getcwd(), 'videos', filename)
    output_path = os.path.join(os.getcwd(), 'videos', f"yolov8_{filename}")
    process_video_yolov8(input_path, output_path)
    return send_from_directory('videos', f"yolov8_{filename}")

@app.route('/videos/<filename>')
def serve_video(filename):
    directory = os.path.join(os.getcwd(), 'videos')
    return send_from_directory(directory, filename)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port = 5000, debug = True)