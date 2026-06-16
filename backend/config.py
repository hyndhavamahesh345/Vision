import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure basic logging for the application
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("visionvault")

load_dotenv(override=True)

BACKEND_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BACKEND_DIR / "uploads")))
FRAMES_DIR = Path(os.getenv("FRAMES_DIR", str(BACKEND_DIR / "frames")))
OUTPUT_DIR = BACKEND_DIR / "output"
ANNOTATED_DIR = BACKEND_DIR / "static" / "annotated"

for d in [UPLOAD_DIR, FRAMES_DIR, OUTPUT_DIR, ANNOTATED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── API / Model Config ────────────────────────────────────────────────────────
USE_HYBRID         = os.getenv("USE_HYBRID", "true").lower() == "true"
USE_GROUNDINGDINO  = False
FLORENCE_MODEL     = os.getenv("FLORENCE_MODEL", "microsoft/Florence-2-base")

FAST_MODE    = os.getenv("FAST_MODE", "false").lower() == "true"
YOLO_WEIGHTS = os.getenv("YOLO_WEIGHTS", str(BACKEND_DIR / "weights" / "yolo11s.pt"))

if FAST_MODE:
    logger.info("[Config] FAST_MODE enabled — applying faster defaults")
    YOLO_CONF_OVERRIDE = float(os.getenv("YOLO_CONF_FAST", "0.28"))
else:
    YOLO_CONF_OVERRIDE = None

default_max_frames = "30"
default_frame_quality = "60" if FAST_MODE else "80"

MAX_FRAMES                = int(os.getenv("MAX_FRAMES", default_max_frames))
FRAME_INTERVAL_SEC        = float(os.getenv("FRAME_INTERVAL_SEC", "2.0"))
FRAME_QUALITY             = int(os.getenv("FRAME_QUALITY", default_frame_quality))

YOLO_CONF_THRESHOLD = float(os.getenv("YOLO_CONF", "0.08"))
CLIP_SCORE_THRESHOLD = float(os.getenv("CLIP_SCORE", "0.25"))
if FAST_MODE and YOLO_CONF_OVERRIDE is not None:
    YOLO_CONF_THRESHOLD = YOLO_CONF_OVERRIDE

MIN_PERSIST_FRAMES = int(os.getenv("MIN_PERSIST_FRAMES", "1"))
TRACK_DETECTION_CONF = float(os.getenv("TRACK_DETECTION_CONF", "0.15"))
TEMPORAL_MIN_AVG_CONF = float(os.getenv("TEMPORAL_MIN_AVG_CONF", "0.05"))

YOLO_INPUT_TARGET_WIDTH = int(os.getenv("YOLO_INPUT_TARGET_WIDTH", "640"))
YOLO_INFER_IMGSZ = int(os.getenv("YOLO_INFER_IMGSZ", "640"))

USE_OBJECT_TRACKING = False
USE_SCENE_MAX_FALLBACK = True
NMS_THRESHOLD = 0.45
