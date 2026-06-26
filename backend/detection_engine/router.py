from config import logger
from detection_engine import tier2_yolov12_world as t2
from detection_engine import tier1_yolo26 as t1

def route_frame(frame_path: str, strategy: str = "yolo-world", job_id: str = None, frame_idx: int = None):
    """
    Routes a frame through the detection tiers.
    """
    detections = []
    
    # Run Tier 1 (Standard YOLO)
    t1_detections = t1.analyze_frame(frame_path, job_id=job_id, frame_idx=frame_idx)
    if t1_detections:
        detections.extend(t1_detections)
        
    # Run Tier 2 (YOLO-World)
    t2_detections = t2.analyze_frame(frame_path, job_id=job_id, frame_idx=frame_idx)
    if t2_detections:
        detections.extend(t2_detections)
        
    if job_id is not None and frame_idx is not None:
        from config import ANNOTATED_DIR
        from aggregator.aggregator import CLASS_THRESHOLDS, DEFAULT_THRESH
        from services.inventory.builder import normalize_object_name, UNIQUE_HOUSEHOLD_OBJECTS
        import cv2
        import supervision as sv
        import numpy as np
        
        try:
            img = cv2.imread(frame_path)
            
            box_annotator = sv.BoxAnnotator(thickness=3)
            label_annotator = sv.LabelAnnotator(text_scale=1.2, text_thickness=2, text_padding=10)
            
            boxes = []
            confidences = []
            valid_detections = []
            
            for d in detections:
                canonical = normalize_object_name(d["label"])
                target_thresh = CLASS_THRESHOLDS.get(canonical, DEFAULT_THRESH)
                
                if d["confidence"] >= target_thresh:
                    boxes.append(d["bbox"])
                    
                    # Temporarily boost Tier 1 confidence so it always wins NMS against Tier 2
                    conf = d["confidence"]
                    if d["tier"] == 1:
                        conf += 2.0
                    confidences.append(conf)
                    
                    valid_detections.append(d)
                    
            if boxes:
                original_indices = np.arange(len(boxes))
                sv_dets = sv.Detections(
                    xyxy=np.array(boxes),
                    confidence=np.array(confidences),
                    class_id=original_indices
                )
                
                # Apply cross-tier NMS to delete overlapping false positives
                sv_dets = sv_dets.with_nms(threshold=0.50, class_agnostic=True)
                kept_indices = sv_dets.class_id.tolist()
                
                for tier in [1, 2]:
                    tier_boxes = []
                    tier_labels = []
                    
                    for idx in kept_indices:
                        d = valid_detections[idx]
                        if d["tier"] == tier:
                            tier_boxes.append(d["bbox"])
                            tier_labels.append(f'{d["label"]} {d["confidence"]:.2f}')
                            
                    if not tier_boxes:
                        continue
                        
                    tier_sv_dets = sv.Detections(
                        xyxy=np.array(tier_boxes),
                        confidence=np.ones(len(tier_boxes)),
                        class_id=np.zeros(len(tier_boxes))
                    )
                    
                    if tier == 1:
                        color = sv.Color(0, 255, 0)
                    elif tier == 2:
                        color = sv.Color(255, 0, 0)
                    else:
                        color = sv.Color(255, 165, 0) # Orange for Tier 3
                        
                    box_annotator.color = color
                    label_annotator.color = color
                    
                    img = box_annotator.annotate(scene=img, detections=tier_sv_dets)
                    img = label_annotator.annotate(scene=img, detections=tier_sv_dets, labels=tier_labels)
                    
            cv2.imwrite(str(ANNOTATED_DIR / f"{job_id}_{frame_idx}.jpg"), img)
        except Exception as e:
            logger.error(f"Failed to save annotated frame: {e}")
            
    return detections
