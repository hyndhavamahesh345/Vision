from config import logger
from detection_engine import grounding_dino as gd
from detection_engine import florence as f2
from detection_engine import custom_yolo as cy
from detection_engine import yolo_world as yw
from detection_engine import coco_yolo as coco
from services.inventory.builder import CORE_HOUSEHOLD_OBJECTS

def route_frame(frame_path: str, strategy: str = "custom-yolo", job_id: str | None = None, frame_idx: int | None = None):
    """
    Routes a frame through the detection engine using Custom YOLO by default.
    """
    detections_list = []
    
    try:
        import cv2
        img = cv2.imread(frame_path)
        if img is None:
            return detections_list
            
        all_sv_dets = []
            
        if strategy == "custom-yolo":
            # Run the Hybrid Custom + COCO YOLO Ensemble for maximum accuracy
            sv_dets_custom = cy.analyze_frame(img, threshold=0.01)
            if sv_dets_custom and len(sv_dets_custom) > 0:
                all_sv_dets.append(sv_dets_custom)
                
            sv_dets_coco = coco.analyze_frame(img, threshold=0.15)
            if sv_dets_coco and len(sv_dets_coco) > 0:
                all_sv_dets.append(sv_dets_coco)
                
        elif strategy == "yolo-world":
            sv_dets = yw.analyze_frame(img, threshold=0.05)
            if sv_dets and len(sv_dets) > 0:
                all_sv_dets.append(sv_dets)
                
        elif strategy == "grounding-dino":
            # GroundingDINO max token limit is 256. We chunk CORE_HOUSEHOLD_OBJECTS.
            # CORE is ~55 objects. Chunking by 30 gives exactly 2 passes per frame!
            unique_core = list(set(CORE_HOUSEHOLD_OBJECTS))
            chunk_size = 30 
            
            for i in range(0, len(unique_core), chunk_size):
                chunk = unique_core[i:i + chunk_size]
                text_prompt = " . ".join(chunk) + " ."
                
                # Analyze using the unified GroundingDINO tier
                sv_dets = gd.analyze_frame(img, text_prompt, threshold=0.15)
                if sv_dets and len(sv_dets) > 0:
                    all_sv_dets.append(sv_dets)
                    
        elif strategy == "florence":
            sv_dets = f2.analyze_frame(img, task_prompt="<OD>")
            if sv_dets and len(sv_dets) > 0:
                # Map Florence-2 outputs to our core objects if needed
                all_sv_dets.append(sv_dets)
            
        for sv_dets in all_sv_dets:
            import numpy as np
            class_names_list = list(sv_dets.data["class_name"])
            for j in range(len(sv_dets)):
                bbox = sv_dets.xyxy[j].tolist()
                conf = float(sv_dets.confidence[j]) if sv_dets.confidence is not None else 1.0
                class_name = class_names_list[j]
                
                # Apply Appliance Brand OCR extraction
                from services.ocr.ocr_processor import OCR_ELAPSED_CLASSES, extract_brand_from_crop
                if class_name in OCR_ELAPSED_CLASSES:
                    h, w = img.shape[:2]
                    xmin = max(0, int(bbox[0]))
                    ymin = max(0, int(bbox[1]))
                    xmax = min(w, int(bbox[2]))
                    ymax = min(h, int(bbox[3]))
                    
                    if (xmax - xmin) > 10 and (ymax - ymin) > 10:
                        crop_img = img[ymin:ymax, xmin:xmax]
                        brand = extract_brand_from_crop(crop_img)
                        if brand:
                            class_name = f"{brand} {class_name}"
                            class_names_list[j] = class_name
                
                detections_list.append({
                    "label": class_name,
                    "confidence": conf,
                    "bbox": bbox,
                    "tier": 1,
                    "frame_idx": frame_idx
                })
            sv_dets.data["class_name"] = np.array(class_names_list)
                
        # Optional: Annotate the image
        if job_id is not None and frame_idx is not None and len(all_sv_dets) > 0:
            from config import ANNOTATED_DIR
            import supervision as sv
            import numpy as np
            
            # Merge detections for annotation
            merged_xyxy = np.vstack([d.xyxy for d in all_sv_dets])
            merged_conf = np.concatenate([d.confidence for d in all_sv_dets])
            merged_class_id = np.concatenate([d.class_id for d in all_sv_dets])
            
            merged_class_names = []
            for d in all_sv_dets:
                merged_class_names.extend(d.data["class_name"])
                
            merged_sv_dets = sv.Detections(
                xyxy=merged_xyxy,
                confidence=merged_conf,
                class_id=merged_class_id
            )
            
            box_annotator = sv.BoxAnnotator(thickness=3)
            label_annotator = sv.LabelAnnotator(text_scale=1.2, text_thickness=2, text_padding=10)
            
            labels = [f"{merged_class_names[k]} {float(merged_conf[k]):.2f}" for k in range(len(merged_conf))]
            
            annotated_img = box_annotator.annotate(scene=img.copy(), detections=merged_sv_dets)
            annotated_img = label_annotator.annotate(scene=annotated_img, detections=merged_sv_dets, labels=labels)
            
            cv2.imwrite(str(ANNOTATED_DIR / f"{job_id}_{frame_idx}.jpg"), annotated_img)
                
    except Exception as e:
        logger.error(f"Failed to process frame with GroundingDINO: {e}")
        import traceback
        traceback.print_exc()
        
    return detections_list
