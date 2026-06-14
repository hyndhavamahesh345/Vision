from typing import List, Dict, Any
from config import YOLO_CONF_THRESHOLD, YOLO_INFER_IMGSZ, logger
from services.inventory.builder import normalize_object_name
from db.postgres import SessionLocal, Job

def run_bytetrack(model, frames: List[str], job_id: str = None) -> List[Dict[int, Dict[str, Any]]]:
    """
    Runs YOLOv11 inference with ByteTrack tracking enabled across a sequence of frames.
    Returns a list (one per frame) of active tracks.
    """
    logger.info("[ByteTrack] Starting tracking on %d frames", len(frames))
    
    # Store results per frame
    # Each frame has a dict mapping track_id -> {"label": str, "bbox": List[float], "conf": float}
    tracked_sequence: List[Dict[int, Dict[str, Any]]] = []
    
    try:
        # Use track instead of predict for authentic temporal tracking across frames
        # persist=True ensures track IDs are maintained across the sequence
        # agnostic_nms=True with iou=0.45 guarantees that overlapping boxes (like 'chair' and 'furniture' on the same object) are merged.
        results = model.track(
            source=frames,
            conf=YOLO_CONF_THRESHOLD,
            iou=0.45,
            agnostic_nms=True,
            imgsz=YOLO_INFER_IMGSZ,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False,
            stream=True
        )
        
        for idx, result in enumerate(results):
            frame_tracks = {}
            boxes = getattr(result, "boxes", None)
            
            if boxes is not None and len(boxes) > 0:
                cls_ids = boxes.cls.int().tolist()
                confs = boxes.conf.tolist()
                xyxys = boxes.xyxy.tolist()
                
                # Real tracking IDs provided by ByteTrack
                if boxes.id is not None:
                    track_ids = boxes.id.int().tolist()
                else:
                    # Fallback if tracker drops (rare)
                    track_ids = [hash(f"{c}_{i}") % 100000 for i, c in enumerate(cls_ids)]
                
                for det_idx in range(len(cls_ids)):
                    cls_id = cls_ids[det_idx]
                    conf = float(confs[det_idx])
                    bbox = xyxys[det_idx]
                    track_id = track_ids[det_idx]
                    
                    if isinstance(result.names, dict):
                        raw_name = str(result.names.get(int(cls_id), str(cls_id))).lower()
                    else:
                        raw_name = str(result.names[int(cls_id)]).lower() if 0 <= int(cls_id) < len(result.names) else str(cls_id).lower()

                    mapped = normalize_object_name(raw_name)
                    if mapped:
                        frame_tracks[track_id] = {
                            "label": mapped,
                            "bbox": bbox,
                            "conf": conf
                        }
            
            tracked_sequence.append(frame_tracks)
            
            if job_id:
                try:
                    db = SessionLocal()
                    job = db.query(Job).filter(Job.id == job_id).first()
                    if job:
                        job.frames_analyzed = idx + 1
                        db.commit()
                    db.close()
                except Exception as e:
                    logger.error("[ByteTrack] DB update error: %s", e)
            
    except Exception as e:
        logger.exception("[ByteTrack] Error during tracking: %s", e)
        # Fallback to empty tracking if it completely fails
        while len(tracked_sequence) < len(frames):
            tracked_sequence.append({})
            
    return tracked_sequence
