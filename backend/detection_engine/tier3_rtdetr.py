from ultralytics import RTDETR
from config import logger, BACKEND_DIR

_model = None

def get_model():
    global _model
    if _model is None:
        try:
            model_path = BACKEND_DIR / "weights" / "rtdetr-l.pt"
            if not model_path.exists():
                logger.info("Downloading Tier 3 model...")
                _model = RTDETR("rtdetr-l.pt")
            else:
                _model = RTDETR(str(model_path))
            logger.info("Loaded Tier 3 (RT-DETR) Model")
        except Exception as e:
            logger.error(f"Failed to load Tier 3: {e}")
    return _model

def analyze_frame(frame_path: str, job_id: str = None, frame_idx: int = None):
    model = get_model()
    if not model:
        return []
    
    # RTDETR prediction
    res = model.predict(frame_path, verbose=False, conf=0.25, iou=0.60, agnostic_nms=True)[0]
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
                "tier": 3
            })
            
    return detections
