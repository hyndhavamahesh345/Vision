import cv2
import numpy as np
import supervision as sv
from ultralytics import YOLO
from pathlib import Path
from config import logger
from services.inventory.builder import normalize_object_name

_model = None

# Core COCO class IDs that map to our inventory database
COCO_INTEREST_CLASSES = {
    56: "chair",
    57: "sofa",
    59: "bed",
    60: "table",
    61: "toilet",
    62: "tv",
    68: "microwave",
    69: "oven",
    71: "sink",
    72: "refrigerator"
}

def load_model():
    global _model
    if _model is not None:
        return
        
    weights_path = str(Path(__file__).resolve().parent.parent / "weights" / "yolov8n.pt")
    logger.info(f"Loading COCO YOLOv8 Model from {weights_path}...")
    _model = YOLO(weights_path)
    logger.info("COCO YOLO loaded successfully!")

def analyze_frame(img: np.ndarray, threshold: float = 0.25) -> sv.Detections:
    """
    Runs standard COCO YOLOv8 detection on the provided image frame.
    Returns supervision.Detections object containing only classes of interest.
    """
    load_model()
    if _model is None:
        return sv.Detections.empty()
        
    results = _model.predict(img, conf=threshold, verbose=False)
    
    if len(results) == 0 or len(results[0].boxes) == 0:
        return sv.Detections.empty()
        
    result = results[0]
    boxes = result.boxes
    
    # Extract YOLO results into numpy arrays
    xyxy = boxes.xyxy.cpu().numpy()
    confidence = boxes.conf.cpu().numpy()
    class_id = boxes.cls.cpu().numpy().astype(int)
    
    filtered_xyxy = []
    filtered_conf = []
    filtered_class_id = []
    filtered_class_names = []
    
    for i in range(len(class_id)):
        c_id = class_id[i]
        conf = confidence[i]
        
        # Only keep classes of interest (toilets, sinks, chairs, beds, sofas, etc.)
        if c_id not in COCO_INTEREST_CLASSES:
            continue
            
        norm_class = COCO_INTEREST_CLASSES[c_id]
        
        # Apply the same spatial context rules to keep behavior consistent
        # Spatial Rule 1: Wall mirrors are never mounted on the ceiling (N/A for COCO but kept for safety)
        if norm_class == "wall mirror" and xyxy[i][1] < 120:
            continue
            
        filtered_xyxy.append(xyxy[i])
        filtered_conf.append(conf)
        filtered_class_id.append(c_id)
        filtered_class_names.append(norm_class)
        
    if not filtered_xyxy:
        return sv.Detections.empty()
        
    # Create supervision Detections object
    sv_dets = sv.Detections(
        xyxy=np.array(filtered_xyxy),
        confidence=np.array(filtered_conf),
        class_id=np.array(filtered_class_id),
        data={"class_name": np.array(filtered_class_names)}
    )
    
    return sv_dets
