from config import logger
from detection_engine import tier1_yolo26 as t1
from detection_engine import tier2_yolov12_world as t2
from detection_engine import tier3_rtdetr as t3

def route_frame(frame_path: str, strategy: str = "hybrid", job_id: str = None, frame_idx: int = None):
    """
    Routes a frame through the detection tiers.
    """
    if strategy == "yolo11s":
        # Force Tier 1 only (fast mode)
        detections = t1.analyze_frame(frame_path, job_id=None, frame_idx=None)
    else:
        # Hybrid Pipeline
        det1 = t1.analyze_frame(frame_path, job_id=None, frame_idx=None)
        det2 = t2.analyze_frame(frame_path, job_id=None, frame_idx=None)
        det3 = t3.analyze_frame(frame_path, job_id=None, frame_idx=None)
        detections = det1 + det2 + det3
        
    if job_id is not None and frame_idx is not None:
        from config import ANNOTATED_DIR
        from aggregator.aggregator import CLASS_THRESHOLDS, DEFAULT_THRESH
        from services.inventory.builder import normalize_object_name
        import cv2
        
        try:
            img = cv2.imread(frame_path)
            # Sort detections so highest confidence is drawn last (on top)
            detections.sort(key=lambda x: x["confidence"])
            
            for d in detections:
                canonical = normalize_object_name(d["label"])
                target_thresh = CLASS_THRESHOLDS.get(canonical, DEFAULT_THRESH)
                
                # Draw boxes for anything that passes the threshold
                if d["confidence"] >= target_thresh:
                    x1, y1, x2, y2 = map(int, d["bbox"])
                    # Use different colors for different tiers
                    color = (0, 255, 0) if d["tier"] == 1 else ((255, 0, 0) if d["tier"] == 2 else (0, 0, 255))
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                    text = f'{d["label"]} {d["confidence"]:.2f}'
                    cv2.putText(img, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                    
            cv2.imwrite(str(ANNOTATED_DIR / f"{job_id}_{frame_idx}.jpg"), img)
        except Exception as e:
            logger.error(f"Failed to save annotated frame: {e}")
            
    return detections
