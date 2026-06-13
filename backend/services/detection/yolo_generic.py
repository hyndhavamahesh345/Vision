from typing import List
from config import YOLO_WEIGHTS, YOLO_CONF_THRESHOLD, YOLO_INFER_IMGSZ, logger
from models.state import _yolo_lock
from services.inventory.builder import HOUSEHOLD_OBJECTS, normalize_object_name

_yolo_model = None

def get_yolo_model():
    global _yolo_model
    if _yolo_model is None:
        with _yolo_lock:
            if _yolo_model is None:
                try:
                    from ultralytics import YOLO
                    logger.info("[YOLO] Loading weights: %s", YOLO_WEIGHTS)
                    _yolo_model = YOLO(YOLO_WEIGHTS)
                    if "world" in YOLO_WEIGHTS.lower():
                        _yolo_model.set_classes(HOUSEHOLD_OBJECTS)
                        logger.info("[YOLO-World] Configured custom vocabulary with %d items.", len(HOUSEHOLD_OBJECTS))
                    logger.info("[YOLO] Model loaded successfully: %s", YOLO_WEIGHTS)
                except Exception as e:
                    logger.exception("[YOLO] Failed to load model: %s", e)
                    _yolo_model = None
    return _yolo_model

def run_yolo_on_frame(model, frame_path: str) -> List[str]:
    """Run YOLO inference on a single frame (for diagnostics compatibility)."""
    try:
        results = model(frame_path, verbose=False, conf=YOLO_CONF_THRESHOLD, imgsz=YOLO_INFER_IMGSZ)
        names: List[str] = []
        for r in results:
            cls_ids = []
            try:
                cls_ids = r.boxes.cls.int().tolist()
            except Exception:
                try:
                    cls_ids = [int(x) for x in r.boxes.cls.tolist()]
                except Exception:
                    cls_ids = []
            for cls_id in cls_ids:
                raw_name = r.names.get(cls_id, str(cls_id)).lower() if isinstance(r.names, dict) else r.names[int(cls_id)].lower()
                mapped = normalize_object_name(raw_name)
                if mapped:
                    names.append(mapped)
        return names
    except Exception as e:
        logger.exception("[YOLO] Inference error: %s", e)
        return []
