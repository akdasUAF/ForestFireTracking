from ultralytics import YOLO

# load your wandb configuration here

# Load a model
model = YOLO('yolov8n-obb.yaml')  # build a new model from YAML
# load a pretrained model (recommended for training)
model = YOLO('yolov8n-obb.pt')
# build from YAML and transfer weights
model = YOLO('yolov8n-obb.yaml').load('yolov8n-obb.pt')

# Train the model
results = model.train(data='/content/data.yaml',  # change it to the path to the data.yaml file for the no augmented dataset

                      epochs=200,

                      resume=True,  # checkpointing,

                      save_period=25,

                      plots=True,  # saving plots

                      # dfl=0.25,#weight of dfl loss

                      # box=8.5,#weight of box loss

                      single_cls=True,  # treats allclasses as singleclass

                      save=True,

                      project="/content/output"
                      )
