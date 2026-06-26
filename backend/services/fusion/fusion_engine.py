import time
from typing import Dict, List, Any, Tuple, Set
from config import logger, MIN_PERSIST_FRAMES, TEMPORAL_MIN_AVG_CONF
from services.detection.yolo_generic import get_yolo_model
from services.detection.yolo_household import get_household_yolo_model, run_household_yolo
from services.video.quality_filter import frame_quality_check
from services.tracking.bytetrack import run_bytetrack

def run_simulated_pipeline(job_id: str, frames: List[str]) -> List[List[str]]:
    import random
    time.sleep(2)
    inventory = ["sofa", "tv", "chair", "bed", "refrigerator"]
    return [random.sample(inventory, k=random.randint(1, 3)) for _ in frames]

def run_hybrid_pipeline(job_id: str, video_path: str, frames: List[str]) -> Tuple[str, List[List[str]]]:
    yolo = get_yolo_model()
    yolo_household = get_household_yolo_model()
    
    if not yolo:
        return "simulated", run_simulated_pipeline(job_id, frames)

    sub = "yolo11s + household + bytetrack"

    # Filter bad frames
    filtered_frames: List[str] = []
    filtered_indices: List[int] = []
    for idx, frame_path in enumerate(frames):
        ok, reasons = frame_quality_check(frame_path)
        if ok:
            filtered_frames.append(frame_path)
            filtered_indices.append(idx)

    if not filtered_frames:
        logger.warning("[%s] No frames passed quality filter", job_id)
        return sub, [[] for _ in frames]

    # If the highly accurate YOLO-World household model is available, use ONLY it to prevent base model noise
    if yolo_household:
        from services.inventory.builder import HOUSEHOLD_OBJECTS
        
        # Combine our standard household objects
        combined_classes = list(set(HOUSEHOLD_OBJECTS + ["side profile air conditioner", "furniture"]))
        
        # 3. Inject the combined vocabulary into YOLO-World's brain
        logger.info("[Fusion] Updating YOLO-World vocabulary with %d total classes", len(combined_classes))
        yolo_household.set_classes(combined_classes)
        
        # 4. Run the high-speed YOLO-World detector on all frames
        tracked_sequence = run_household_yolo(yolo_household, filtered_frames, job_id=job_id)
        sub = "yolov8x-worldv2"
    else:
        # Fallback to base yolo
        tracked_sequence = run_bytetrack(yolo, filtered_frames, job_id=job_id)
        sub = "yolo11s + bytetrack"

    # Compile tracks and filter out transients
    # Since we use agnostic_nms to prevent spatial duplicates, and max_counts to prevent temporal duplicates,
    # we can bypass strict temporal persistence filtering to ensure all objects are returned.
    
    final_frames: List[List[str]] = [[] for _ in frames]
    for frame_idx, frame_tracks in enumerate(tracked_sequence):
        for track_id, info in frame_tracks.items():
            final_frames[frame_idx].append(info["label"])

    return sub, final_frames
