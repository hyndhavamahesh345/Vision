from ultralytics import YOLO

# Load a pre-trained small model to start with, this trains much faster
model = YOLO('yolov8n.pt')

# Train on our massive custom dataset
# We use 15 epochs to balance speed and accuracy since there are 2334 images
print("Starting YOLO custom training on 2334 images...")
results = model.train(
    data='dataset/dataset.yaml', 
    epochs=3, 
    imgsz=640, 
    device='cpu', 
    name='household_model_massive'
)
print("Training complete! The best model is saved in runs/detect/household_model_massive/weights/best.pt")
