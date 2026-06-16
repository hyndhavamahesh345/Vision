from ultralytics import YOLO
from config import logger, BACKEND_DIR
import os

_model = None

def get_model():
    global _model
    if _model is None:
        try:
            # We use yolov8n as the "YOLO26" primary fast model
            model_path = BACKEND_DIR / "weights" / "yolov8n.pt"
            if not model_path.exists():
                logger.info("Downloading Tier 1 model...")
                _model = YOLO("yolov8n.pt")
            else:
                _model = YOLO(str(model_path))
            logger.info("Loaded Tier 1 (YOLO26) Model")
        except Exception as e:
            logger.error(f"Failed to load Tier 1: {e}")
    return _model

def analyze_frame(frame_path: str, job_id: str = None, frame_idx: int = None):
    model = get_model()
    if not model:
        return []
    
    res = model.predict(frame_path, verbose=False, conf=0.15, iou=0.60, agnostic_nms=True)[0]
    detections = []
    
    if res.boxes is not None and len(res.boxes) > 0:
        cls_ids = res.boxes.cls.int().tolist()
        confs = res.boxes.conf.tolist()
        xyxys = res.boxes.xyxy.tolist()
        
        for i in range(len(cls_ids)):
            label = res.names[cls_ids[i]].lower()
            detections.append({
                "label": label,
                "confidence": float(confs[i]),
                "bbox": xyxys[i],
                "tier": 1
            })
            
    return detections
