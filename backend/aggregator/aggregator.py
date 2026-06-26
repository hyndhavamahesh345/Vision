from typing import List, Dict, Any
from services.inventory.builder import normalize_object_name

CLASS_THRESHOLDS = {
    "air conditioner": 0.12,
    "ac": 0.12,
    "ceiling fan": 0.05,
    "table fan": 0.05,
    "pedestal fan": 0.05,
    "wall fan": 0.05,
    "fan": 0.05,
    "chair": 0.12,
    "office chair": 0.12,
    "dining chair": 0.12,
    "gaming chair": 0.12,
    "bar stool": 0.12,
    "sofa": 0.35,
    "l-shaped sofa": 0.35,
    "desk": 0.35,
    "chair": 0.35,
    "table": 0.12,
    "light": 0.10,
    "ceiling light": 0.10,
    "wall light": 0.10,
    "lamp": 0.12,
    "floor lamp": 0.15,
    "table lamp": 0.15,
    "chandelier": 0.10,
    "television": 0.15,
    "tv": 0.15,
    "monitor": 0.15,
    "cupboard": 0.12,
    "cabinet": 0.12,
    "refrigerator": 0.20,
    "furniture": 0.12,
    "bed": 0.15,
    "bunk bed": 0.15,
    "microwave": 0.15,
    "oven": 0.15,
    "washing machine": 0.15,
    "picture frame": 0.25,
    "painting": 0.25,
    "window": 0.12,
    "door": 0.10,
    "light switch": 0.08,
    "bathtub": 0.25,
    "sink": 0.10,
    "shower": 0.10,
    "toilet": 0.10,
    "geyser": 0.01,
    "water heater": 0.01,
    "bench": 0.15,
    "rug": 0.25,
    "carpet": 0.25,
    "mat": 0.12,
    "bulb": 0.10,
    "light bulb": 0.10,
    "exhaust fan": 0.08,
    "diwan cot": 0.15,
    "divan cot": 0.15,
    "dishwasher": 0.15,
    "dryer": 0.15,
    "stove": 0.15,
    "plant": 0.12,
    "bottle": 0.12,
    "mop": 0.12,
    "broom": 0.12,
    "bucket": 0.12,
    "gate": 0.12,
    "tv unit": 0.12,
    "dressing table": 0.12,
    "curtain": 0.12,
    "blinds": 0.12,
    "water purifier": 0.12,
    "gas cylinder": 0.12,
    "mixer grinder": 0.12,
    "trash can": 0.12,
    "balcony railing": 0.10,
    "swing": 0.12,
    "inverter": 0.12,
    "chimney": 0.10,
    "unknown object": 0.25
}
DEFAULT_THRESH = 0.12
UNCERTAIN_THRESH = 0.08
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

def aggregate_detections(all_frame_detections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates detections using both Scene-Max and Tracking, maintaining dual-validation logic.
    """
    from config import USE_OBJECT_TRACKING, USE_SCENE_MAX_FALLBACK, NMS_THRESHOLD, logger
    import supervision as sv
    import numpy as np
    from services.inventory.builder import UNIQUE_HOUSEHOLD_OBJECTS

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
    
    # Scene-Max Storage
    class_frame_counts: Dict[str, set] = {} 
    max_counts_per_class: Dict[str, int] = {}
    uncertain_candidates: set = set()
    
    # ByteTrack Storage (Initialize with low activation threshold so our custom thresholds dictate tracking)
    tracker = sv.ByteTrack(track_activation_threshold=0.05) if USE_OBJECT_TRACKING else None
    tracked_unique_objects: Dict[str, set] = {}
    
    sorted_frame_indices = sorted(frame_groups.keys())
    
    for f_idx in sorted_frame_indices:
        raw_detections = frame_groups[f_idx]
        
        # 1. Filter raw detections and prepare for supervision
        boxes = []
        confidences = []
        class_ids = []
        
        for det in raw_detections:
            raw_label = det.get("label")
            conf = det.get("confidence", 0)
            bbox = det.get("bbox", [0,0,0,0])
            
            if raw_label:
                canonical = normalize_object_name(raw_label)
                if not canonical:
                    continue
                    
                target_thresh = CLASS_THRESHOLDS.get(canonical, DEFAULT_THRESH)
                
                if conf >= target_thresh or conf >= UNCERTAIN_THRESH:
                    # Tiered Priority Boosting to force correct NMS hierarchy
                    # Tier 1 (Highest Priority) - Structural/Large fixtures
                    if canonical in {"chandelier", "ceiling fan", "fan", "geyser", "water heater", "bunk bed", "diwan cot", "divan cot", "exhaust fan", "wall fan", "light", "wall light", "ceiling light", "lamp"}:
                        conf += 2.0
                    # Tier 2 (Medium Priority) - Specific furniture items
                    elif canonical in {"office chair", "gaming chair", "dining chair", "bar stool", "floor lamp", "wall light", "ceiling light", "table fan", "pedestal fan", "table lamp"}:
                        conf += 1.0
                        
                    boxes.append(bbox)
                    confidences.append(conf)
                    try:
                        c_id = UNIQUE_HOUSEHOLD_OBJECTS.index(canonical)
                    except ValueError:
                        c_id = -1
                    class_ids.append(c_id)
        
        # 2. Run NMS with supervision
        if boxes:
            detections = sv.Detections(
                xyxy=np.array(boxes),
                confidence=np.array(confidences),
                class_id=np.array(class_ids)
            )
            # Remove invalid class_ids (-1)
            valid_mask = detections.class_id != -1
            detections = detections[valid_mask]
            
            if len(detections) > 0:
                # Apply NMS to suppress overlapping boxes across tiers (Cross-Tier NMS)
                detections = detections.with_nms(threshold=0.50, class_agnostic=True)
                
                # Restore original confidences by removing the boost
                detections.confidence = detections.confidence % 1.0
                
                # --- SCENE-MAX LOGIC ---
                if USE_SCENE_MAX_FALLBACK:
                    frame_counts: Dict[str, int] = {}
                    for i in range(len(detections)):
                        c_id = detections.class_id[i]
                        conf = detections.confidence[i]
                        canonical = UNIQUE_HOUSEHOLD_OBJECTS[c_id]
                        target_thresh = CLASS_THRESHOLDS.get(canonical, DEFAULT_THRESH)
                        
                        if conf >= target_thresh:
                            frame_counts[canonical] = frame_counts.get(canonical, 0) + 1
                        elif conf >= UNCERTAIN_THRESH:
                            uncertain_candidates.add(canonical)
                            
                    for label, count in frame_counts.items():
                        max_counts_per_class[label] = max(max_counts_per_class.get(label, 0), count)
                        if label not in class_frame_counts:
                            class_frame_counts[label] = set()
                        class_frame_counts[label].add(f_idx)
                
                # --- BYTETRACK LOGIC ---
                if USE_OBJECT_TRACKING and tracker:
                    # Tracker requires detections to be updated
                    tracked_dets = tracker.update_with_detections(detections)
                    for i in range(len(tracked_dets)):
                        c_id = tracked_dets.class_id[i]
                        tracker_id = tracked_dets.tracker_id[i]
                        conf = tracked_dets.confidence[i]
                        canonical = UNIQUE_HOUSEHOLD_OBJECTS[c_id]
                        target_thresh = CLASS_THRESHOLDS.get(canonical, DEFAULT_THRESH)
                        
                        if conf >= target_thresh:
                            if canonical not in tracked_unique_objects:
                                tracked_unique_objects[canonical] = set()
                            tracked_unique_objects[canonical].add(tracker_id)
        else:
            if USE_OBJECT_TRACKING and tracker:
                tracker.update_with_detections(sv.Detections.empty())
            
    # Resolve Final Inventory
    inventory_list = []
    uncertain_final = []
    
    # Store dual validation data
    validation_data = {}
    
    # Compile Scene-Max Results
    scene_max_inventory = {}
    for label, count in max_counts_per_class.items():
        if len(class_frame_counts[label]) >= MIN_TEMPORAL_FRAMES:
            scene_max_inventory[label] = count
            if label in uncertain_candidates:
                uncertain_candidates.remove(label)
        else:
            uncertain_candidates.add(label)
            
    # Compile ByteTrack Results
    tracking_inventory = {}
    for label, id_set in tracked_unique_objects.items():
        tracking_inventory[label] = len(id_set)
        
    # Populate inventory_list (prefer Tracking if enabled, but never drop below Scene-Max bounds)
    primary_inventory = {}
    all_possible_labels = set(scene_max_inventory.keys()).union(set(tracking_inventory.keys()))
    # Items that are almost always singular per room and prone to track fragmentation
    SINGLE_INSTANCE_ITEMS = {
        "geyser", "water heater", "refrigerator", "fridge", "television", "tv",
        "washing machine", "stove", "microwave", "oven", "bathtub", "shower",
        "pedestal fan", "ceiling fan", "fan", "wall fan", "bed", "sink", "toilet"
    }
    
    if USE_OBJECT_TRACKING:
        for label in all_possible_labels:
            t_count = tracking_inventory.get(label, 0)
            s_count = scene_max_inventory.get(label, 0)
            
            if label in SINGLE_INSTANCE_ITEMS:
                # Cap to 1 to completely prevent duplicates in standard rooms
                primary_inventory[label] = 1 if (s_count > 0 or t_count > 0) else 0
            else:
                # Tracking can drop tracks on sparse frames. SceneMax is a guaranteed minimum bound.
                primary_inventory[label] = max(t_count, s_count)
    else:
        primary_inventory = {}
        for label, s_count in scene_max_inventory.items():
            if label in SINGLE_INSTANCE_ITEMS:
                primary_inventory[label] = 1 if s_count > 0 else 0
            else:
                primary_inventory[label] = s_count
    # --- SEMANTIC DEDUPLICATION ---
    # Removes generic objects if a more specific version was found in the same room
    dedup_rules = {
        "sofa": ["couch", "settee"],
        "l-shaped sofa": ["sofa", "couch"],
        "armchair": ["chair"],
        "gaming chair": ["chair", "office chair"],
        "dining chair": ["chair"],
        "office chair": ["chair"],
        "bar stool": ["chair", "stool"],
        "coffee table": ["table"],
        "dining table": ["table"],
        "desk": ["table"],
        "ceiling fan": ["fan"],
        "pedestal fan": ["fan"],
        "wall fan": ["fan"],
        "exhaust fan": ["fan"],
        "bunk bed": ["bed"],
        "diwan cot": ["bed", "cot"],
        "divan cot": ["bed", "cot"],
        "refrigerator": ["fridge"],
        "television": ["tv", "monitor"],
        "tv": ["television", "monitor"],
        "kitchen cabinet": ["cabinet", "cupboard"],
        "wardrobe": ["closet", "cabinet", "cupboard"],
        "chandelier": ["ceiling light", "lamp", "light"],
        "floor lamp": ["lamp", "light"],
        "table lamp": ["lamp", "light"],
        "wall light": ["lamp", "ceiling light", "light"],
        "ceiling light": ["light", "lamp"],
        "lamp": ["light"],
        "geyser": ["water heater", "bathroom water heater", "water boiler", "water tank", "hot water dispenser", "water cylinder"],
        "water heater": ["geyser", "bathroom water heater", "water boiler", "water tank", "hot water dispenser", "water cylinder"],
        "curtain": ["blinds"],
        "trash can": ["dustbin", "bin"],
        "dustbin": ["trash can", "bin"],
        "ro purifier": ["water purifier"],
        "water purifier": ["ro purifier"],
        "carpet": ["rug"],
        "rug": ["carpet"],
        "cushion": ["pillow"],
        "pillow": ["cushion"]
    }
    
    keys_to_remove = set()
    active_labels = list(primary_inventory.keys())
    
    for specific_item, generic_items in dedup_rules.items():
        if specific_item in active_labels:
            for generic_item in generic_items:
                if generic_item in active_labels:
                    keys_to_remove.add(generic_item)
                    
    for k in keys_to_remove:
        if k in primary_inventory:
            del primary_inventory[k]
            
    for label, count in primary_inventory.items():
        inventory_list.append({
            "name": label,
            "quantity": count
        })
        
    for label in uncertain_candidates:
        uncertain_final.append(label)
        
    # Generate Comparison Logs
    all_labels = set(scene_max_inventory.keys()).union(set(tracking_inventory.keys()))
    for label in all_labels:
        s_count = scene_max_inventory.get(label, 0)
        t_count = tracking_inventory.get(label, 0)
        validation_data[label] = {
            "tracking_count": t_count,
            "scene_max_count": s_count
        }
        if s_count != t_count:
            logger.warning(f"Validation Discrepancy for '{label}': Tracked={t_count}, SceneMax={s_count}")
            
    return {
        "inventory": inventory_list,
        "uncertain": uncertain_final,
        "total_frames_analyzed": total_frames_analyzed,
        "processing_tier_breakdown": tier_counts,
        "validation_data": validation_data
    }
