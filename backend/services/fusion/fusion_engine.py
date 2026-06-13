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
        tracked_sequence = run_household_yolo(yolo_household, filtered_frames)
        sub = "yolov8x-worldv2 exclusively"
    else:
        # Fallback to base yolo
        tracked_sequence = run_bytetrack(yolo, filtered_frames)
        sub = "yolo11s + bytetrack"

    # Compile tracks and filter out transients
    track_history: Dict[int, Dict[str, Any]] = {}
    
    for frame_idx, frame_tracks in enumerate(tracked_sequence):
        for track_id, info in frame_tracks.items():
            if track_id not in track_history:
                track_history[track_id] = {
                    "label": info["label"],
                    "frames_seen": set(),
                    "confs": [],
                    "best_conf": 0.0
                }
            
            state = track_history[track_id]
            state["frames_seen"].add(frame_idx)
            state["confs"].append(info["conf"])
            if info["conf"] > state["best_conf"]:
                state["best_conf"] = info["conf"]

    accepted_track_ids: Set[int] = set()
    for track_id, state in track_history.items():
        frames_seen = len(state["frames_seen"])
        avg_conf = sum(state["confs"]) / max(1, len(state["confs"]))
        best_conf = state["best_conf"]
        
        # Keep tracks that persist across multiple frames, or very high confidence single detections
        # Using best_conf instead of avg_conf prevents blurry frames from lowering the average and dropping the track
        if (frames_seen >= MIN_PERSIST_FRAMES or (frames_seen >= 1 and best_conf > 0.45)) and best_conf >= TEMPORAL_MIN_AVG_CONF:
            accepted_track_ids.add(track_id)

    # Generate final detections format for compatibility
    final_frames: List[List[str]] = [[] for _ in frames]
    for track_id, state in track_history.items():
        if track_id in accepted_track_ids:
            for frame_idx in state["frames_seen"]:
                final_frames[frame_idx].append(state["label"])

    return sub, final_frames
