import cv2
import torch
from pathlib import Path
import supervision as sv
import numpy as np
from ultralytics import YOLO
from config import logger

_model = None

def load_model():
    global _model
    if _model is not None:
        return
        
    weights_path = Path(__file__).parent.parent / "weights" / "visionvault_yolov8.pt"
    if not weights_path.exists():
        logger.error(f"Custom YOLO model not found at {weights_path}!")
        return
        
    logger.info(f"Loading Custom YOLOv8 Model from {weights_path}...")
    _model = YOLO(str(weights_path))
    logger.info("Custom YOLO loaded successfully!")

def analyze_frame(img: np.ndarray, threshold: float = 0.25) -> sv.Detections:
    """
    Runs the custom YOLO model on the provided image frame.
    Returns supervision.Detections object for easy downstream integration.
    """
    load_model()
    if _model is None:
        return sv.Detections.empty()
        
    # YOLO automatically uses CPU/GPU based on availability and internally resizes
    results = _model.predict(img, conf=threshold, verbose=False)
    
    if len(results) == 0 or len(results[0].boxes) == 0:
        return sv.Detections.empty()
        
    result = results[0]
    boxes = result.boxes
    
    # Extract YOLO results into numpy arrays
    xyxy = boxes.xyxy.cpu().numpy()
    confidence = boxes.conf.cpu().numpy()
    class_id = boxes.cls.cpu().numpy().astype(int)
    
    from aggregator.aggregator import CLASS_THRESHOLDS, DEFAULT_THRESH
    from services.inventory.builder import normalize_object_name
    
    filtered_xyxy = []
    filtered_conf = []
    filtered_class_id = []
    filtered_class_names = []
    
    # Check if this frame contains bathroom-related objects
    has_bathroom = any(normalize_object_name(_model.names[c]) in {"toilet", "sink", "geyser", "shower", "bathtub"} for c in class_id)
    
    for i in range(len(class_id)):
        c_id = class_id[i]
        conf = confidence[i]
        raw_class = _model.names[c_id]
        norm_class = normalize_object_name(raw_class)
        
        if not norm_class:
            continue
            
        # Spatial Rule 1: Wall mirrors are never mounted on the ceiling
        if norm_class == "wall mirror" and xyxy[i][1] < 120:  # ymin < 120px
            continue
            
        # Context Rule 2: Bathroom frames don't contain living room chairs (usually misclassified washbasins)
        if has_bathroom and norm_class == "chair":
            norm_class = "sink"
            
        target_thresh = CLASS_THRESHOLDS.get(norm_class, DEFAULT_THRESH)
        if conf >= target_thresh:
            filtered_xyxy.append(xyxy[i])
            filtered_conf.append(conf)
            filtered_class_id.append(c_id)
            filtered_class_names.append(norm_class)
            
    if not filtered_xyxy:
        return sv.Detections.empty()
        
    sv_dets = sv.Detections(
        xyxy=np.array(filtered_xyxy),
        confidence=np.array(filtered_conf),
        class_id=np.array(filtered_class_id),
        data={"class_name": np.array(filtered_class_names)}
    )
    
    return sv_dets
