import cv2
import torch
from pathlib import Path
import supervision as sv
import numpy as np
from ultralytics import YOLOWorld
from config import logger
from services.inventory.builder import CORE_HOUSEHOLD_OBJECTS, normalize_object_name

_model = None
unique_core = list(set(CORE_HOUSEHOLD_OBJECTS))
unique_core.sort()
class_map = {name: i for i, name in enumerate(unique_core)}

def load_model():
    global _model
    if _model is not None:
        return
        
    logger.info(f"Loading YOLOv8s-World Model...")
    # This will automatically download the 25MB weights to the ultralytics cache if not present
    _model = YOLOWorld("yolov8s-world.pt")
    _model.set_classes(unique_core)
    logger.info("YOLO-World loaded successfully!")

def analyze_frame(img: np.ndarray, threshold: float = 0.05) -> sv.Detections:
    """
    Runs YOLO-World zero-shot detection on the provided image frame.
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
    class_id_model = boxes.cls.cpu().numpy().astype(int)
    
    from aggregator.aggregator import CLASS_THRESHOLDS, DEFAULT_THRESH, UNCERTAIN_THRESH
    
    filtered_xyxy = []
    filtered_conf = []
    filtered_class_id = []
    filtered_class_names = []
    
    raw_dets = []
    for i in range(len(class_id_model)):
        c_id = class_id_model[i]
        conf = confidence[i]
        raw_class = unique_core[c_id]
        norm_class = normalize_object_name(raw_class)
        if norm_class:
            raw_dets.append({
                "xyxy": xyxy[i],
                "conf": conf,
                "c_id": c_id,
                "name": norm_class
            })
            
    # Check if a sofa is detected in this frame with reasonable confidence
    has_sofa = any(d["name"] in {"sofa", "l-shaped sofa"} and d["conf"] >= 0.15 for d in raw_dets)
    # Check if this frame contains bathroom-related objects
    has_bathroom = any(d["name"] in {"toilet", "sink", "geyser", "shower", "bathtub"} for d in raw_dets)
    
    for d in raw_dets:
        name = d["name"]
        conf = d["conf"]
        
        # Spatial Rule 1: Wall mirrors are never mounted on the ceiling
        if name == "wall mirror" and d["xyxy"][1] < 120:  # ymin < 120px
            continue
            
        # Context Rule 2: Bathroom frames don't contain living room chairs
        if has_bathroom and name == "chair":
            name = "sink"
            
        # Suppress bed predictions on sofas in living room frames
        if has_sofa and name in {"bed", "bunk bed", "diwan cot", "divan cot"}:
            continue
            
        target_thresh = CLASS_THRESHOLDS.get(name, DEFAULT_THRESH)
        if conf >= target_thresh:
            filtered_xyxy.append(d["xyxy"])
            filtered_conf.append(conf)
            filtered_class_id.append(d["c_id"])
            filtered_class_names.append(name)
            
    if not filtered_xyxy:
        return sv.Detections.empty()
        
    class_names_np = np.array(filtered_class_names)
    
    # Create supervision Detections object
    sv_dets = sv.Detections(
        xyxy=np.array(filtered_xyxy),
        confidence=np.array(filtered_conf),
        class_id=np.array(filtered_class_id),
        data={"class_name": class_names_np}
    )
    
    return sv_dets
