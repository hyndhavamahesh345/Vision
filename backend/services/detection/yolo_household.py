from typing import List, Dict, Any
from ultralytics import YOLO
from config import logger, BACKEND_DIR

# We use our newly trained custom model for accurate detection on this video.
_custom_yolo_model = None

def get_household_yolo_model():
    global _custom_yolo_model
    if _custom_yolo_model is None:
        try:
            # Load the original extra-large zero-shot model from the weights directory
            model_path = str(BACKEND_DIR / "weights" / "yolov8x-worldv2.pt")
            _custom_yolo_model = YOLO(model_path)
            
            # Explicitly define our classes, including the highly specific prompts
            CLASSES = [
                "projector", "chimney", "air conditioner", "table", "chair", 
                "water heater", "ceiling fan", "light switch", "bed", "sofa", 
                "television", "refrigerator", "side profile air conditioner",
                "cabinet", "wardrobe", "furniture"
            ]
            _custom_yolo_model.set_classes(CLASSES)
            logger.info("Successfully loaded Zero-Shot YOLO-World Detection Model.")
        except Exception as e:
            logger.error(f"Failed to load custom model: {e}")
            return None
    return _custom_yolo_model

def run_household_yolo(model, frames: List[str]) -> List[Dict[int, Dict[str, Any]]]:
    """
    Runs raw YOLO inference instead of ByteTrack to avoid tracker dropping low confidence detections.
    Assigns sequential fake track IDs.
    """
    logger.info("[YOLO-Household] Running raw prediction on %d frames", len(frames))
    sequence = []
    
    for frame_path in frames:
        frame_tracks = {}
        # Increased confidence threshold to 0.25 to aggressively filter out false positive furniture
        res = model.predict(frame_path, conf=0.25, verbose=False)[0]
        
        boxes = res.boxes
        if boxes is not None and len(boxes) > 0:
            cls_ids = boxes.cls.int().tolist()
            confs = boxes.conf.tolist()
            xyxys = boxes.xyxy.tolist()
            
            counts = {}
            for i in range(len(cls_ids)):
                label = res.names[cls_ids[i]].lower()
                
                # Automatically map the side-profile prompt back to the standard label
                if label == "side profile air conditioner":
                    label = "air conditioner"
                    
                counts[label] = counts.get(label, 0) + 1
                # Stable track ID based on label and instance number to simulate tracking
                stable_track_id = hash(f"{label}_{counts[label]}") % 100000
                
                frame_tracks[stable_track_id] = {
                    "label": label,
                    "bbox": xyxys[i],
                    "conf": float(confs[i])
                }
                
        sequence.append(frame_tracks)
        
    return sequence

