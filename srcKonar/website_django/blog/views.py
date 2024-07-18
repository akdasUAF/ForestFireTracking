from django.shortcuts import render,redirect
from django.http import HttpResponse
from .forms import DemoForm,model_compare_form
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from ultralytics import YOLO
import os
import cv2
from django.shortcuts import render, redirect
from django.conf import settings
from ultralytics import YOLO
import os
import cv2
import os
import cv2
from django.conf import settings
from django.shortcuts import render, redirect
from ultralytics import YOLO
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


# Create your views here.
def home(request):
    # context = {
    #     'posts': posts
    # }
    return render(request,'blog/home.html') #makes data from database accessible to the html files

def about(request):
    return  render(request,'blog/about.html')

def contact(request):
    return render(request,'blog/contact.html')

def model_specification(request):
    return render(request,'blog/model_specification.html')








def try_demo(request):
    model_choices = {
        'small': [('yolov8n.pt', 'YOLOv8-Nano'), ('yolov8s_obb.pt', 'YOLOv8 OBB Small'), ('yolov8n_obb.pt', 'YOLOv8-OBB N')],
        'medium': [('', ''), ('', '')],
        'large': [('', ''), ('', '')]
    }

    if request.method == 'POST':
        form = DemoForm(request.POST, request.FILES)
        size = request.POST.get('size')
        form.fields['model_type'].choices = model_choices.get(size, [])

        if form.is_valid():
            size = form.cleaned_data['size']
            model_type = form.cleaned_data['model_type']
            input_file = request.FILES['input_file']
            conf = form.cleaned_data['conf']
            # Save the uploaded file
            file_name = default_storage.save(input_file.name, ContentFile(input_file.read()))
            # Store the data in the session
            request.session['size'] = size
            request.session['model_type'] = model_type
            request.session['input_file'] = file_name
            request.session['conf']=conf
            return redirect('results')
    else:
        form = DemoForm()

    return render(request, 'blog/try_demo.html', {'form': form})


def results(request):
    size = request.session.get('size')
    model_type = request.session.get('model_type')
    input_file = request.session.get('input_file')
    conf1 = request.session.get('conf')
    if not size or not model_type or not input_file:
        return redirect('try_demo')

    # Load the YOLO model
    model = YOLO(os.path.join(settings.BASE_DIR, 'blog', 'Yolo Weights', model_type))

    # Define the input and output file paths
    input_path = os.path.join(settings.MEDIA_ROOT, input_file)
    output_dir = os.path.join(settings.MEDIA_ROOT, 'output')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'result.jpg')

    # Read the input image
    frame = cv2.imread(input_path)

    # Run inference
    results = model.predict(frame, iou=0.4, conf=float(conf1))

    # Visualize the results on the frame
    annotated_frame = results[0].plot()

    # Save the annotated frame
    cv2.imwrite(output_path, annotated_frame)

    # Ensure the media URL is used in the template context
    output_file_url = os.path.join(settings.MEDIA_URL, 'output/result.jpg')

    return render(request, 'blog/results.html', {
        'size': size,
        'model_type': model_type,
        'input_file': input_file,
        'output_file': output_file_url,  # Update this path
        'conf': conf1,
    })


def model_compare(request):
    # model_choices = {
    #     'small': [('yolov8n.pt', 'YOLOv8-Nano'), ('yolov8s.pt', 'YOLOv8-Small'), ('yolov8n_obb.pt', 'YOLOv8-Oriented Bounding Boxes')],
    #     'medium': [('', ''), ('', '')],
    #     'large': [('', ''), ('', '')]
    # }

    if request.method == 'POST':
        form = model_compare_form(request.POST, request.FILES)
        size = request.POST.get('size')
        # form.fields['model_type'].choices = model_choices.get(size, [])

        if form.is_valid():
            size = form.cleaned_data['size']
            # model_type = form.cleaned_data['model_type']
            input_file = request.FILES['input_file']
            # Save the uploaded file
            file_name = default_storage.save(input_file.name, ContentFile(input_file.read()))
            # Store the data in the session
            request.session['size'] = size
            # request.session['model_type'] = model_type
            request.session['input_file'] = file_name
            return redirect('model_compare_results')
    else:
        form = model_compare_form()

    return render(request, 'blog/model_compare.html', {'form': form})


def model_compare_results(request):
    size = request.session.get('size')
    input_file = request.session.get('input_file')

    if not size or not input_file:
        return redirect('try_demo')

    model_choices = {
        'small': ['yolov8n.pt', 'yolov8s_obb.pt', 'yolov8n_obb.pt'],
        'medium': [],
        'large': [],
    }

    output_files = []

    for model_type in model_choices[size]:
        model = YOLO(os.path.join(settings.BASE_DIR, 'blog', 'Yolo Weights', model_type))

        # Define the input and output file paths
        input_path = os.path.join(settings.MEDIA_ROOT, input_file)
        output_dir = os.path.join(settings.MEDIA_ROOT, 'output_model_compare')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'result_{model_type}.jpg')

        # Read the input image
        frame = cv2.imread(input_path)
        # Run inference
        results = model.track(frame, iou=0.05, persist=True)
        # Visualize the results on the frame
        annotated_frame = results[0].plot()
        # Save the annotated frame
        cv2.imwrite(output_path, annotated_frame)
        # Ensure the media URL is used in the template context
        output_files.append({
            'url': os.path.join(settings.MEDIA_URL, 'output_model_compare', f'result_{model_type}.jpg'),
            'model_type': model_type
        })

    return render(request, 'blog/model_compare_results.html', {
        'size': size,
        'input_file': input_file,
        'output_files': output_files  # Pass the list of dictionaries
    })

    
    
