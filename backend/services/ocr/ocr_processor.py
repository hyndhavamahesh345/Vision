import cv2
import numpy as np
from pathlib import Path
from config import logger

_reader = None

BRANDS = {
    "samsung": "Samsung",
    "lg": "LG",
    "sony": "Sony",
    "havells": "Havells",
    "whirlpool": "Whirlpool",
    "panasonic": "Panasonic",
    "daikin": "Daikin",
    "voltas": "Voltas",
    "hitachi": "Hitachi",
    "godrej": "Godrej",
    "ifb": "IFB",
    "bosch": "Bosch",
    "philips": "Philips",
    "luminous": "Luminous",
    "bisleri": "Bisleri",
    "kinley": "Kinley",
    "milton": "Milton",
    "havel": "Havells",
    "samsung": "Samsung",
}

# Only run OCR on objects that typically have prominent brand labels
OCR_ELAPSED_CLASSES = {
    "refrigerator",
    "washing machine",
    "microwave",
    "oven",
    "tv",
    "television",
    "monitor",
    "geyser",
    "water heater",
    "air conditioner",
    "ac",
    "bottle",
    "pedestal fan",
    "table fan"
}

def get_reader():
    global _reader
    if _reader is None:
        try:
            import easyocr
            logger.info("[OCR] Loading EasyOCR English reader model...")
            _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            logger.info("[OCR] EasyOCR loaded successfully.")
        except Exception as e:
            logger.error("[OCR] Failed to load EasyOCR: %s", e)
            _reader = None
    return _reader

def extract_brand_from_crop(crop_img: np.ndarray) -> str | None:
    """
    Runs OCR on the cropped bounding box image and checks for known appliance brands.
    """
    reader = get_reader()
    if reader is None or crop_img is None or crop_img.size == 0:
        return None
        
    try:
        # Run EasyOCR text detection & recognition
        results = reader.readtext(crop_img)
        
        for bbox, text, conf in results:
            if not text:
                continue
            
            clean_text = text.lower().strip()
            # Check for substring matches in brands dictionary
            for kw, brand_name in BRANDS.items():
                if kw in clean_text:
                    logger.info("[OCR] Detected brand '%s' from text '%s' (conf: %.2f)", brand_name, text, conf)
                    return brand_name
    except Exception as e:
        logger.error("[OCR] Inference error: %s", e)
        
    return None
