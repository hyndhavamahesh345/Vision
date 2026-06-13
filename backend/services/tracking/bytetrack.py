from typing import List, Dict, Any
from config import YOLO_CONF_THRESHOLD, YOLO_INFER_IMGSZ, logger
from services.inventory.builder import normalize_object_name

def run_bytetrack(model, frames: List[str]) -> List[Dict[int, Dict[str, Any]]]:
    """
    Runs YOLOv11 inference with ByteTrack tracking enabled across a sequence of frames.
    Returns a list (one per frame) of active tracks.
    """
    logger.info("[ByteTrack] Starting tracking on %d frames", len(frames))
    
    # Store results per frame
    # Each frame has a dict mapping track_id -> {"label": str, "bbox": List[float], "conf": float}
    tracked_sequence: List[Dict[int, Dict[str, Any]]] = []
    
    try:
        # Use predict instead of track to bypass the tracker's hardcoded confidence thresholds
        # This is critical for blurry WhatsApp videos where confidence might be 15-20%
        results = model.predict(
            source=frames,
            conf=YOLO_CONF_THRESHOLD,
            imgsz=YOLO_INFER_IMGSZ,
            verbose=False,
            stream=True
        )
        
        for result in results:
            frame_tracks = {}
            boxes = getattr(result, "boxes", None)
            
            if boxes is not None and len(boxes) > 0:
                cls_ids = boxes.cls.int().tolist()
                confs = boxes.conf.tolist()
                xyxys = boxes.xyxy.tolist()
                
                counts = {}
                for det_idx in range(len(cls_ids)):
                    cls_id = cls_ids[det_idx]
                    conf = float(confs[det_idx])
                    bbox = xyxys[det_idx]
                    
                    if isinstance(result.names, dict):
                        raw_name = str(result.names.get(int(cls_id), str(cls_id))).lower()
                    else:
                        raw_name = str(result.names[int(cls_id)]).lower() if 0 <= int(cls_id) < len(result.names) else str(cls_id).lower()

                    counts[raw_name] = counts.get(raw_name, 0) + 1
                    track_id = hash(f"{raw_name}_{counts[raw_name]}") % 100000

                    mapped = normalize_object_name(raw_name)
                    if mapped:
                        frame_tracks[track_id] = {
                            "label": mapped,
                            "bbox": bbox,
                            "conf": conf
                        }
            
            tracked_sequence.append(frame_tracks)
            
    except Exception as e:
        logger.exception("[ByteTrack] Error during tracking: %s", e)
        # Fallback to empty tracking if it completely fails
        while len(tracked_sequence) < len(frames):
            tracked_sequence.append({})
            
    return tracked_sequence
