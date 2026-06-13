import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
from typing import Optional

from config import logger

_mobilenet_model = None
_imagenet_labels = None

def get_mobilenet_model():
    global _mobilenet_model, _imagenet_labels
    if _mobilenet_model is None:
        try:
            logger.info("[RoomClassifier] Loading MobileNetV3-Small...")
            weights = models.MobileNet_V3_Small_Weights.DEFAULT
            _mobilenet_model = models.mobilenet_v3_small(weights=weights)
            _mobilenet_model.eval()
            _imagenet_labels = weights.meta["categories"]
            logger.info("[RoomClassifier] MobileNetV3 loaded successfully.")
        except Exception as e:
            logger.exception("[RoomClassifier] Failed to load MobileNetV3: %s", e)
            _mobilenet_model = None
    return _mobilenet_model

def get_local_room_assignment(obj_name: str, frame_path: Optional[str] = None) -> str:
    """Classifies the room using basic rules, optionally enhanced by MobileNetV3."""
    name = str(obj_name).lower()
    
    # 1. First Pass: Taxonomy Rules
    bedroom_items = ["bed", "wardrobe", "closet", "nightstand", "pillow", "blanket", "drawer"]
    bathroom_items = ["toilet", "bathtub", "shower", "mirror", "toothbrush", "hair drier"]
    kitchen_items = ["refrigerator", "fridge", "microwave", "oven", "stove", "dishwasher", "toaster", "kettle", "cupboard", "cabinet", "dining table", "sink faucet", "kitchen sink"]
    
    for b in bedroom_items:
        if b in name: return "Bedroom"
    for b in bathroom_items:
        if b in name: return "Bathroom"
    for k in kitchen_items:
        if k in name: return "Kitchen"

    # 2. Second Pass: If ambiguous like "sink" or "chair", use MobileNetV3 on the frame
    if frame_path and (name == "sink" or name == "chair" or name == "table"):
        model = get_mobilenet_model()
        if model:
            try:
                img = Image.open(frame_path).convert("RGB")
                transform = models.MobileNet_V3_Small_Weights.DEFAULT.transforms()
                batch = transform(img).unsqueeze(0)
                
                with torch.no_grad():
                    prediction = model(batch).squeeze(0).softmax(0)
                    top_prob, top_catid = torch.topk(prediction, 1)
                    label = _imagenet_labels[top_catid[0].item()].lower()
                    
                    if "bathroom" in label or "washbasin" in label or "tub" in label:
                        return "Bathroom"
                    if "kitchen" in label or "dining" in label:
                        return "Kitchen"
            except Exception as e:
                logger.warning("[RoomClassifier] Inference failed for %s: %s", name, e)

    return "Living Room"
