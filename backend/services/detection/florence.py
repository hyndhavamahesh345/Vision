import os
import torch
from PIL import Image
from typing import List
from config import logger, FLORENCE_MODEL

_florence_model = None
_florence_processor = None
_device = "cuda" if torch.cuda.is_available() else "cpu"

def load_florence_model():
    """Loads the Florence-2 model and processor lazily."""
    global _florence_model, _florence_processor
    
    if _florence_model is None or _florence_processor is None:
        try:
            from transformers import AutoProcessor, AutoModelForCausalLM
            logger.info("[Florence-2] Downloading and loading the vision-language model. This may take a moment...")
            
            # Load processor (native support, no trust_remote_code needed)
            _florence_processor = AutoProcessor.from_pretrained(FLORENCE_MODEL)
            
            # Load model
            _florence_model = AutoModelForCausalLM.from_pretrained(FLORENCE_MODEL).to(_device).eval()
            
            logger.info("[Florence-2] Successfully loaded on %s", _device)
        except Exception as e:
            logger.error("[Florence-2] Failed to load model: %s", e)
            return False
            
    return True

def generate_dynamic_vocabulary(frame_path: str) -> List[str]:
    """
    Takes a single frame, runs Florence-2 Object Detection (<OD>), 
    and extracts a unique list of detected object names.
    """
    if not load_florence_model():
        return []
        
    try:
        logger.info("[Florence-2] Generating dynamic vocabulary for frame: %s", frame_path)
        image = Image.open(frame_path).convert("RGB")
        
        # We use <OD> (Object Detection) to find all objects in the scene
        task_prompt = "<OD>"
        
        inputs = _florence_processor(text=task_prompt, images=image, return_tensors="pt").to(_device)
        
        with torch.no_grad():
            generated_ids = _florence_model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=1024,
                num_beams=3,
                do_sample=False
            )
            
        generated_text = _florence_processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
        parsed_answer = _florence_processor.post_process_generation(generated_text, task=task_prompt, image_size=(image.width, image.height))
        
        # Florence <OD> format usually returns a dict with 'bboxes' and 'labels'
        detected_objects = set()
        
        if "<OD>" in parsed_answer:
            labels = parsed_answer["<OD>"].get("labels", [])
            for label in labels:
                clean_label = label.lower().strip()
                if clean_label:
                    detected_objects.add(clean_label)
                    
        unique_objects = list(detected_objects)
        logger.info("[Florence-2] Dynamically discovered %d objects: %s", len(unique_objects), unique_objects)
        return unique_objects
        
    except Exception as e:
        logger.error("[Florence-2] Error generating vocabulary: %s", e)
        return []
