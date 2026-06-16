from ultralytics import YOLOWorld
from config import logger, BACKEND_DIR
from services.inventory.builder import UNIQUE_HOUSEHOLD_OBJECTS

_model = None

def get_model():
    global _model
    if _model is None:
        try:
            model_path = BACKEND_DIR / "weights" / "yolov8x-worldv2.pt"
            logger.info("Initializing Tier 2 (YOLOv12-World)...")
            _model = YOLOWorld('yolov8s-world.pt')
            _model.set_classes(UNIQUE_HOUSEHOLD_OBJECTS)
            logger.info("Tier 2 ready.")
        except Exception as e:
            logger.error(f"Failed to load Tier 2: {e}")
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
                "tier": 2,
                "frame_idx": frame_idx
            })
            
    if job_id is not None and frame_idx is not None:
        from config import ANNOTATED_DIR
        from aggregator.aggregator import CLASS_THRESHOLDS, DEFAULT_THRESH
        from services.inventory.builder import normalize_object_name
        import cv2
        
        try:
            img = cv2.imread(frame_path)
            for d in detections:
                canonical = normalize_object_name(d["label"])
                target_thresh = CLASS_THRESHOLDS.get(canonical, DEFAULT_THRESH)
                
                # Only draw the box if it passes the aggregator's strict threshold
                if d["confidence"] >= target_thresh:
                    x1, y1, x2, y2 = map(int, d["bbox"])
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    text = f'{d["label"]} {d["confidence"]:.2f}'
                    cv2.putText(img, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    
            cv2.imwrite(str(ANNOTATED_DIR / f"{job_id}_{frame_idx}.jpg"), img)
        except Exception as e:
            logger.error(f"Failed to save annotated frame: {e}")
            
    return detections
