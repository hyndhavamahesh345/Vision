import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from yolo_household import get_household_yolo_model

print("Testing get_household_yolo_model()...")
model = get_household_yolo_model()
if model is not None:
    print("Model loaded successfully!")
    print(model)
else:
    print("Failed to load model.")
