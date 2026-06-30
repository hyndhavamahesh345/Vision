import torch
from transformers import AutoProcessor, AutoModelForCausalLM
from config import logger
import supervision as sv
import cv2
import numpy as np
from PIL import Image

_model = None
_processor = None

def load_model():
    global _model, _processor
    if _model is not None:
        return

    model_id = 'microsoft/Florence-2-base-ft'
    logger.info(f"Downloading/Loading Florence-2 ({model_id})...")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Bugfix for transformers > 4.41.2 with Florence-2
    from transformers import PretrainedConfig, PreTrainedTokenizerFast, PreTrainedTokenizer, PreTrainedModel
    if not hasattr(PretrainedConfig, 'forced_bos_token_id'):
        PretrainedConfig.forced_bos_token_id = None
        
    # Bugfix for tokenizer missing additional_special_tokens
    def get_ast(self): return getattr(self, '_ast', self.all_special_tokens)
    def set_ast(self, value): self._ast = value
    if not hasattr(PreTrainedTokenizer, 'additional_special_tokens'):
        PreTrainedTokenizer.additional_special_tokens = property(get_ast, set_ast)
    if not hasattr(PreTrainedTokenizerFast, 'additional_special_tokens'):
        PreTrainedTokenizerFast.additional_special_tokens = property(get_ast, set_ast)
        
    # Bugfix for SDPA
    if not hasattr(PreTrainedModel, '_supports_sdpa'):
        PreTrainedModel._supports_sdpa = False
        
    _processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    _model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        trust_remote_code=True,
        attn_implementation="eager"
    ).to(device).eval()
    logger.info(f"Florence-2 loaded on {device}")

def analyze_frame(img: np.ndarray, task_prompt="<OD>") -> sv.Detections:
    """
    Runs Florence-2 Object Detection on the provided image frame.
    """
    load_model()
    assert _model is not None
    assert _processor is not None
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Convert OpenCV BGR to PIL RGB
    image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img_orig = Image.fromarray(image_rgb)
    orig_w, orig_h = pil_img_orig.width, pil_img_orig.height
    
    # Florence-2 transformers bug workaround: force square image
    pil_img = pil_img_orig.resize((768, 768))
    
    inputs = _processor(text=task_prompt, images=pil_img, return_tensors="pt")
    
    inputs = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
    inputs["pixel_values"] = inputs["pixel_values"].to(device, _model.dtype)
    
    with torch.no_grad():
        generated_ids = _model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            early_stopping=False,
            do_sample=False,
            num_beams=1,
            use_cache=False
        )
        
    generated_text = _processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    
    parsed_answer = _processor.post_process_generation(
        generated_text, 
        task=task_prompt, 
        image_size=(orig_w, orig_h)
    )
    
    # <OD> task outputs a dictionary: {'<OD>': {'bboxes': [[...]], 'labels': [...]}}
    predictions = parsed_answer.get(task_prompt, {})
    if not isinstance(predictions, dict):
        return sv.Detections.empty()
        
    bboxes = predictions.get('bboxes', [])
    labels = predictions.get('labels', [])
    
    if not bboxes or not labels:
        return sv.Detections.empty()
        
    bboxes_np = np.array(bboxes)
    
    # Create supervision Detections object
    # Florence-2 does not naturally output confidences for <OD>, so we mock 1.0
    confidences = np.ones(len(bboxes_np))
    
    # Convert string labels to integer class_ids for SV
    class_id = np.arange(len(labels))
    
    # SV expects xyxy format which Florence provides
    sv_dets = sv.Detections(
        xyxy=bboxes_np,
        confidence=confidences,
        class_id=class_id,
        data={"class_name": np.array(labels)}
    )
    
    return sv_dets
