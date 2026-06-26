from ultralytics import YOLOWorld
from config import logger, BACKEND_DIR, YOLO_WORLD_MODEL
from services.inventory.builder import UNIQUE_HOUSEHOLD_OBJECTS

_model = None

def get_model():
    global _model
    if _model is None:
        try:
            from pathlib import Path
            base_path = Path(YOLO_WORLD_MODEL)
            if not base_path.is_absolute():
                base_path = BACKEND_DIR / base_path
            grounded_path = base_path.parent / f"{base_path.stem}_grounded.pt"

            if grounded_path.exists():
                logger.info(f"Initializing Tier 2 with pre-grounded model: {grounded_path.name}...")
                _model = YOLOWorld(str(grounded_path))
                logger.info("Tier 2 ready (Pre-grounded loaded).")
            else:
                logger.info(f"Initializing Tier 2 (YOLO-World: {YOLO_WORLD_MODEL})...")
                _model = YOLOWorld(YOLO_WORLD_MODEL)
                logger.info("Grounding Tier 2 with unique household objects...")
                # Exclude basic COCO classes that Tier 1 handles perfectly
                coco_classes = {"toilet", "sink", "bed", "couch", "sofa", "chair", "tv", "microwave", "oven", "refrigerator", "bottle", "cup", "clock", "vase", "dining table", "potted plant"}
                tier2_classes = [c for c in UNIQUE_HOUSEHOLD_OBJECTS if c not in coco_classes]
                _model.set_classes(tier2_classes)
                logger.info(f"Saving pre-grounded model to {grounded_path.name}...")
                _model.save(str(grounded_path))
                logger.info("Tier 2 ready (Grounded and cached).")
        except Exception as e:
            logger.error(f"Failed to load Tier 2: {e}")
    return _model

def analyze_frame(frame_path: str, job_id: str = None, frame_idx: int = None):
    model = get_model()
    if not model:
        return []
    
    res = model.predict(frame_path, verbose=False, conf=0.01, iou=0.60, agnostic_nms=False, half=False)[0]
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

