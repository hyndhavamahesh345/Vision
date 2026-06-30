from config import logger
import supervision as sv
import cv2
import numpy as np
from PIL import Image

_model = None

def load_model():
    global _model
    if _model is not None:
        return

    import torch
    import transformers

    if not hasattr(transformers.models.bert.modeling_bert.BertModel, "get_head_mask"):
        def get_head_mask(self, head_mask, num_hidden_layers, is_attention_chunked=False):
            return [None] * num_hidden_layers
        transformers.models.bert.modeling_bert.BertModel.get_head_mask = get_head_mask

    from autodistill_grounding_dino import GroundingDINO
    from autodistill.detection import CaptionOntology
    
    logger.info("Downloading/Loading GroundingDINO...")
    _model = GroundingDINO(ontology=CaptionOntology({"dummy": "dummy"}))
    logger.info("GroundingDINO loaded")

def analyze_frame(img: np.ndarray, text_prompt: str, threshold: float = 0.25) -> sv.Detections:
    """
    Runs GroundingDINO Object Detection on the provided image frame with a custom text prompt.
    """
    load_model()
    assert _model is not None
    from autodistill.detection import CaptionOntology
    
    # Update ontology dynamically for the prompt
    classes = [c.strip() for c in text_prompt.split('.') if c.strip()]
    ontology = {c: c for c in classes}
    _model.ontology = CaptionOntology(ontology)
    
    # GroundingDINO uses PIL images
    image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(image_rgb)
    
    # Infer
    results = _model.predict(pil_img)
    
    # Filter by threshold
    valid_indices = results.confidence >= threshold
    filtered_results = results[valid_indices]
    
    if filtered_results and len(filtered_results) > 0:
        filtered_results.data["class_name"] = np.array([classes[i] for i in filtered_results.class_id])
    
    return filtered_results
