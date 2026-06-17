from ultralytics import YOLOWorld
from config import logger, BACKEND_DIR
from services.inventory.builder import UNIQUE_HOUSEHOLD_OBJECTS

_model = None

def get_model():
    global _model
    if _model is None:
        try:
            model_path = BACKEND_DIR / "weights" / "yolov8x-worldv2.pt"
            logger.info("Initializing Tier 2 (YOLO-World XL)...")
            _model = YOLOWorld('yolov8x-worldv2.pt')
            _model.set_classes(UNIQUE_HOUSEHOLD_OBJECTS)
            logger.info("Tier 2 ready.")
        except Exception as e:
            logger.error(f"Failed to load Tier 2: {e}")
    return _model

def analyze_frame(frame_path: str, job_id: str = None, frame_idx: int = None):
    model = get_model()
    if not model:
        return []
    
    res = model.predict(frame_path, verbose=False, conf=0.01, iou=0.60, agnostic_nms=False)[0]
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
                "tier": 2,
                "frame_idx": frame_idx
            })
            
    return detections
