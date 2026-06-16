from config import logger
from detection_engine import tier2_yolov12_world as t2

def route_frame(frame_path: str, strategy: str = "yolo-world", job_id: str = None, frame_idx: int = None):
    """
    Routes a frame through the detection tiers.
    """
    detections = t2.analyze_frame(frame_path, job_id=job_id, frame_idx=frame_idx)
        
    if job_id is not None and frame_idx is not None:
        from config import ANNOTATED_DIR
        from aggregator.aggregator import CLASS_THRESHOLDS, DEFAULT_THRESH
        from services.inventory.builder import normalize_object_name, UNIQUE_HOUSEHOLD_OBJECTS
        import cv2
        import supervision as sv
        import numpy as np
        
        try:
            img = cv2.imread(frame_path)
            
            # Create supervision BoxAnnotator and LabelAnnotator
            box_annotator = sv.BoxAnnotator()
            label_annotator = sv.LabelAnnotator()
            
            # We want to use different colors for different tiers, 
            # so we might need multiple sv.Detections objects or a custom color map,
            # but supervision's BoxAnnotator is easier if we just pass a color palette 
            # or annotate tier by tier. Let's annotate tier by tier for colors.
            
            for tier in [1, 2, 3]:
                tier_detections = [d for d in detections if d["tier"] == tier]
                if not tier_detections:
                    continue
                
                boxes = []
                confidences = []
                class_ids = []
                labels_text = []
                
                for d in tier_detections:
                    canonical = normalize_object_name(d["label"])
                    target_thresh = CLASS_THRESHOLDS.get(canonical, DEFAULT_THRESH)
                    
                    if d["confidence"] >= target_thresh:
                        boxes.append(d["bbox"])
                        confidences.append(d["confidence"])
                        
                        try:
                            c_id = UNIQUE_HOUSEHOLD_OBJECTS.index(canonical)
                        except ValueError:
                            c_id = -1
                        class_ids.append(c_id)
                        labels_text.append(f'{d["label"]} {d["confidence"]:.2f}')
                        
                if boxes:
                    sv_dets = sv.Detections(
                        xyxy=np.array(boxes),
                        confidence=np.array(confidences),
                        class_id=np.array(class_ids)
                    )
                    
                    # Choose color based on tier
                    if tier == 1:
                        color = sv.Color(0, 255, 0)
                    elif tier == 2:
                        color = sv.Color(255, 0, 0)
                    else:
                        color = sv.Color(0, 0, 255)
                        
                    box_annotator.color = color
                    label_annotator.color = color
                    
                    img = box_annotator.annotate(scene=img, detections=sv_dets)
                    img = label_annotator.annotate(scene=img, detections=sv_dets, labels=labels_text)
                    
            cv2.imwrite(str(ANNOTATED_DIR / f"{job_id}_{frame_idx}.jpg"), img)
        except Exception as e:
            logger.error(f"Failed to save annotated frame: {e}")
            
    return detections
