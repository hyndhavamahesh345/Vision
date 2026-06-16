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
        return t1.analyze_frame(frame_path, job_id, frame_idx)
        
    # We now exclusively use Tier 2 (YOLO-World) because we expanded its 
    # vocabulary to cover all 76 household objects. This prevents double 
    # counting and ensures every frame is searched for every object!
    detections = t2.analyze_frame(frame_path, job_id, frame_idx)
    
    return detections
