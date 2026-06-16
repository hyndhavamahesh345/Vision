from typing import List, Dict, Any
from services.inventory.builder import normalize_object_name

CLASS_THRESHOLDS = {
    "air conditioner": 0.20,
    "ceiling fan": 0.20,
    "fan": 0.20,
    "chair": 0.35,
    "sofa": 0.35,
    "table": 0.35,
    "light": 0.20,
    "ceiling light": 0.20,
    "lamp": 0.25,
    "chandelier": 0.20,
    "television": 0.20,
    "tv": 0.20,
    "monitor": 0.20,
    "cupboard": 0.20,
    "cabinet": 0.20,
    "refrigerator": 0.40,
    "bed": 0.35,
    "microwave": 0.40,
    "oven": 0.40,
    "washing machine": 0.40,
    "picture frame": 0.60,
    "painting": 0.60,
    "window": 0.20,
    "door": 0.20,
    "light switch": 0.15,
    "bathtub": 0.70,
    "sink": 0.70,
    "shower": 0.70,
    "toilet": 0.70
}
DEFAULT_THRESH = 0.35
UNCERTAIN_THRESH = 0.25
MIN_TEMPORAL_FRAMES = 1

def compute_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    interArea = max(0, x2 - x1) * max(0, y2 - y1)
    if interArea == 0:
        return 0

    box1Area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2Area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    return interArea / float(box1Area + box2Area - interArea)

def run_nms(detections: List[Dict[str, Any]], iou_thresh: float = 0.45) -> List[Dict[str, Any]]:
    sorted_dets = sorted(detections, key=lambda x: x.get("confidence", 0), reverse=True)
    kept = []
    for det in sorted_dets:
        overlap = False
        for k_det in kept:
            if compute_iou(det.get("bbox", [0,0,0,0]), k_det.get("bbox", [0,0,0,0])) > iou_thresh:
                overlap = True
                break
        if not overlap:
            kept.append(det)
    return kept

def aggregate_detections(all_frame_detections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates detections using Scene-Max + Temporal Confirmation.
    """
    frame_groups: Dict[int, List[Dict[str, Any]]] = {}
    tier_counts = {"tier1": 0, "tier2": 0, "tier3": 0}
    
    for det in all_frame_detections:
        f_idx = det.get("frame_idx", 0)
        if f_idx not in frame_groups:
            frame_groups[f_idx] = []
        frame_groups[f_idx].append(det)
        
        tier = det.get("tier", 1)
        tier_counts[f"tier{tier}"] += 1

    total_frames_analyzed = len(frame_groups)
    
    class_frame_counts: Dict[str, set] = {} 
    max_counts_per_class: Dict[str, int] = {}
    uncertain_candidates: set = set()
    
    for f_idx, raw_detections in frame_groups.items():
        # Apply NMS to remove duplicates across models within the same frame
        detections = run_nms(raw_detections, iou_thresh=0.45)
        
        frame_counts: Dict[str, int] = {}
        for det in detections:
            raw_label = det.get("label")
            conf = det.get("confidence", 0)
            bbox = det.get("bbox", [0,0,0,0])
            
            if raw_label:
                canonical = normalize_object_name(raw_label)
                if not canonical:
                    continue
                    
                target_thresh = CLASS_THRESHOLDS.get(canonical, DEFAULT_THRESH)
                
                # Sanity rule: Reject very small hallucinated bounding boxes (<400px area)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                area = w * h
                if area < 400:
                    continue
                
                if conf >= target_thresh:
                    frame_counts[canonical] = frame_counts.get(canonical, 0) + 1
                elif conf >= UNCERTAIN_THRESH:
                    uncertain_candidates.add(canonical)
                    
        for label, count in frame_counts.items():
            max_counts_per_class[label] = max(max_counts_per_class.get(label, 0), count)
            if label not in class_frame_counts:
                class_frame_counts[label] = set()
            class_frame_counts[label].add(f_idx)
            
    # Apply temporal confirmation
    inventory_list = []
    uncertain_final = []
    
    for label, count in max_counts_per_class.items():
        if len(class_frame_counts[label]) >= MIN_TEMPORAL_FRAMES:
            inventory_list.append({
                "name": label,
                "quantity": count
            })
            if label in uncertain_candidates:
                uncertain_candidates.remove(label)
        else:
            # Appeared but not in enough frames
            uncertain_candidates.add(label)
            
    for label in uncertain_candidates:
        uncertain_final.append(label)
        
    return {
        "inventory": inventory_list,
        "uncertain": uncertain_final,
        "total_frames_analyzed": total_frames_analyzed,
        "processing_tier_breakdown": tier_counts
    }
