import os
import json
import uuid
import time
import re
import base64
from pathlib import Path
from typing import Dict, List, Any, Tuple
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import cv2
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="VisionVault API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten to your Vercel URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
FRAMES_DIR = Path(os.getenv("FRAMES_DIR", "./frames"))
OUTPUT_DIR = Path("./output")
for d in [UPLOAD_DIR, FRAMES_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── API / model config ────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("MODEL", "gemini-2.0-flash")
OLLAMA_URL     = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "llava")
USE_HYBRID     = os.getenv("USE_HYBRID", "true").lower() == "true"
USE_FLORENCE   = os.getenv("USE_FLORENCE", "true").lower() == "true"
FLORENCE_MODEL = os.getenv("FLORENCE_MODEL", "microsoft/Florence-2-base")

# ── Speed tuning ──────────────────────────────────────────────────────────────
YOLO_GAP_THRESHOLD       = int(os.getenv("YOLO_GAP_THRESHOLD", "4"))
MAX_FRAMES               = int(os.getenv("MAX_FRAMES", "12"))
FRAME_INTERVAL_SEC       = float(os.getenv("FRAME_INTERVAL_SEC", "3.0"))
MAX_LLAVA_CALLS          = int(os.getenv("MAX_LLAVA_CALLS", "0"))
FRAME_QUALITY            = int(os.getenv("FRAME_QUALITY", "80"))
YOLO_SKIP_FLORENCE_TOTAL = int(os.getenv("YOLO_SKIP_FLORENCE_TOTAL", "12"))
MAX_FLORENCE_CALLS       = int(os.getenv("MAX_FLORENCE_CALLS", "4"))

processing_jobs: Dict[str, Dict[str, Any]] = {}

# ── YOLO model (lazy-loaded once) ─────────────────────────────────────────────
_yolo_model = None

def get_yolo_model():
    global _yolo_model
    if _yolo_model is None:
        try:
            from ultralytics import YOLO
            _yolo_model = YOLO("yolo11s.pt")   # small — good balance of speed + accuracy on CPU
            print("[YOLO] Model loaded: yolo11s")
        except Exception as e:
            print(f"[YOLO] Failed to load model: {e}")
            _yolo_model = False
    return _yolo_model if _yolo_model else None


# ── Florence-2 model (lazy-loaded once) ───────────────────────────────────────
_florence_model = None
_florence_processor = None

def get_florence_model():
    global _florence_model, _florence_processor
    if _florence_model is None:
        try:
            import torch
            from transformers import AutoProcessor, AutoModelForCausalLM
            print(f"[Florence-2] Loading {FLORENCE_MODEL} — first run downloads ~1.5GB...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype  = torch.float16 if device == "cuda" else torch.float32
            _florence_processor = AutoProcessor.from_pretrained(
                FLORENCE_MODEL, trust_remote_code=True
            )
            _florence_model = AutoModelForCausalLM.from_pretrained(
                FLORENCE_MODEL, torch_dtype=dtype, trust_remote_code=True
            ).to(device)
            _florence_model.eval()
            print(f"[Florence-2] Loaded on {device}")
        except Exception as e:
            print(f"[Florence-2] Failed to load: {e}")
            _florence_model = False
            _florence_processor = False
    return (_florence_model, _florence_processor) if _florence_model else (None, None)

# ── Ollama availability check (lazy) ─────────────────────────────────────────
_ollama_available = None

def is_ollama_available() -> bool:
    global _ollama_available
    if _ollama_available is not None:
        return _ollama_available
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3.0)
        models = [m["name"] for m in r.json().get("models", [])]
        _ollama_available = any(OLLAMA_MODEL in m for m in models)
        if _ollama_available:
            print(f"[Ollama] Available — model '{OLLAMA_MODEL}' found")
        else:
            print(f"[Ollama] Running but model '{OLLAMA_MODEL}' not pulled. Run: ollama pull {OLLAMA_MODEL}")
    except Exception:
        _ollama_available = False
        print("[Ollama] Not running or unreachable")
    return _ollama_available

# ── Household vocabulary ──────────────────────────────────────────────────────
HOUSEHOLD_OBJECTS = [
    "sofa", "couch", "chair", "armchair", "table", "dining table", "coffee table",
    "desk", "tv", "television", "monitor", "bed", "mattress", "wardrobe", "closet",
    "cabinet", "cupboard", "refrigerator", "fridge", "fan", "ceiling fan", "light",
    "lamp", "chandelier", "door", "window", "shelf", "bookshelf", "rack",
    "clock", "rug", "carpet", "curtain", "blinds", "plant", "potted plant",
    "washing machine", "microwave", "oven", "stove", "sink", "toilet", "bathtub",
    "shower", "mirror", "picture frame", "painting", "pillow", "cushion",
    "blanket", "air conditioner", "heater", "fireplace", "staircase",
    "drawer", "nightstand", "bench", "ottoman", "bookcase", "kettle",
    "toaster", "dishwasher", "dryer", "iron", "vacuum", "printer",
    "speaker", "router", "phone", "laptop", "computer",
]

CANONICAL = {
    "couch": "sofa", "settee": "sofa",
    "armchair": "chair", "recliner": "chair", "stool": "chair",
    "dining table": "table", "coffee table": "table", "desk": "table",
    "side table": "table", "end table": "table", "nightstand": "table",
    "bedside table": "table",
    "television": "tv", "monitor": "tv", "screen": "tv",
    "mattress": "bed", "bunk bed": "bed",
    "closet": "wardrobe", "cupboard": "wardrobe", "cabinet": "wardrobe",
    "drawer": "wardrobe",
    "fridge": "refrigerator", "freezer": "refrigerator",
    "ceiling fan": "fan", "table fan": "fan", "pedestal fan": "fan",
    "lamp": "light", "chandelier": "light", "ceiling light": "light",
    "wall light": "light", "bulb": "light",
    "bookshelf": "shelf", "bookcase": "shelf", "rack": "shelf",
    "carpet": "rug", "mat": "rug",
    "blinds": "curtain", "drapes": "curtain",
    "potted plant": "plant", "indoor plant": "plant", "flower": "plant",
    "washing machine": "appliance", "microwave": "appliance",
    "oven": "appliance", "stove": "appliance", "kettle": "appliance",
    "toaster": "appliance", "dishwasher": "appliance", "dryer": "appliance",
    "iron": "appliance", "vacuum": "appliance",
    "ottoman": "chair", "bench": "chair",
    "picture frame": "wall decor", "painting": "wall decor",
    "pillow": "cushion",
    "air conditioner": "appliance", "heater": "appliance",
    # YOLO class names → household names
    "person": None,          # skip people
    "bicycle": None,
    "car": None,
    "motorcycle": None,
    "airplane": None,
    "bus": None,
    "train": None,
    "truck": None,
    "boat": None,
    "traffic light": None,
    "fire hydrant": None,
    "stop sign": None,
    "parking meter": None,
    "bench": "chair",
    "bird": "plant",         # treat as decor
    "cat": None,
    "dog": None,
    "horse": None,
    "sheep": None,
    "cow": None,
    "elephant": None,
    "bear": None,
    "zebra": None,
    "giraffe": None,
    "backpack": None,
    "umbrella": None,
    "handbag": None,
    "tie": None,
    "suitcase": None,
    "frisbee": None,
    "skis": None,
    "snowboard": None,
    "sports ball": None,
    "kite": None,
    "baseball bat": None,
    "baseball glove": None,
    "skateboard": None,
    "surfboard": None,
    "tennis racket": None,
    "bottle": None,
    "wine glass": None,
    "cup": None,
    "fork": None,
    "knife": None,
    "spoon": None,
    "bowl": None,
    "banana": None,
    "apple": None,
    "sandwich": None,
    "orange": None,
    "broccoli": None,
    "carrot": None,
    "hot dog": None,
    "pizza": None,
    "donut": None,
    "cake": None,
    "potted plant": "plant",
    "dining table": "table",
    "toilet": "toilet",
    "tv": "tv",
    "laptop": "laptop",
    "mouse": None,
    "remote": None,
    "keyboard": None,
    "cell phone": None,
    "microwave": "appliance",
    "oven": "appliance",
    "toaster": "appliance",
    "sink": "sink",
    "refrigerator": "refrigerator",
    "book": None,
    "clock": "clock",
    "vase": "plant",
    "scissors": None,
    "teddy bear": None,
    "hair drier": "appliance",
    "toothbrush": None,
}

class InventoryItem(BaseModel):
    name: str
    quantity: int


# ═══════════════════════════════════════════════════════════════════════════════
#  API ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    allowed = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {allowed}")

    job_id = str(uuid.uuid4())
    video_path = UPLOAD_DIR / f"{job_id}{ext}"
    with open(video_path, "wb") as f:
        f.write(await file.read())

    processing_jobs[job_id] = {
        "status": "uploaded",
        "video_name": file.filename,
        "frames_extracted": 0,
        "frames_analyzed": 0,
        "inventory": [],
        "error": None,
        "pipeline": "initializing",
    }

    # Fire-and-forget in a background thread — returns immediately so frontend can poll
    import threading
    t = threading.Thread(target=process_video, args=(job_id, str(video_path)), daemon=True)
    t.start()

    return {"job_id": job_id, "message": "Processing started"}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    j = processing_jobs[job_id]
    return {
        "job_id": job_id,
        "status": j["status"],           # uploaded | extracting | analyzing | merging | completed | error
        "video_name": j["video_name"],
        "frames_extracted": j.get("frames_extracted", 0),
        "frames_analyzed": j.get("frames_analyzed", 0),
        "pipeline": j.get("pipeline", "initializing"),
        "error": j.get("error"),
    }


@app.get("/api/inventory/{job_id}")
async def get_inventory(job_id: str):
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    j = processing_jobs[job_id]
    if j["status"] != "completed":
        return {"job_id": job_id, "status": j["status"], "video_name": j["video_name"], "inventory": []}
    return {
        "job_id": job_id,
        "status": "completed",
        "video_name": j["video_name"],
        "total_frames": j.get("frames_extracted", 0),
        "inventory": j["inventory"],
        "pipeline": j.get("pipeline", "unknown"),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.get("/api/health")
async def health():
    yolo_ready     = get_yolo_model() is not None
    ollama_ready   = is_ollama_available()
    florence_ready = get_florence_model()[0] is not None
    gemini_ready   = bool(GEMINI_API_KEY)

    if gemini_ready:
        active_pipeline = "gemini"
    elif USE_HYBRID:
        parts = []
        if yolo_ready: parts.append("yolo")
        if USE_FLORENCE and florence_ready and MAX_FLORENCE_CALLS > 0:
            parts.append("florence-2")
        elif ollama_ready and MAX_LLAVA_CALLS > 0:
            parts.append("llava")
        active_pipeline = " + ".join(parts) if parts else "yolo-only"
    else:
        active_pipeline = "simulated"

    return {
        "status": "healthy",
        "active_pipeline": active_pipeline,
        "gemini_api_key_set": gemini_ready,
        "yolo_available": yolo_ready,
        "florence_available": florence_ready,
        "florence_model": FLORENCE_MODEL,
        "ollama_available": ollama_ready,
        "use_hybrid": USE_HYBRID,
        "use_florence": USE_FLORENCE,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ═══════════════════════════════════════════════════════════════════════════════
#  VIDEO PROCESSING PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def process_video(job_id: str, video_path: str):
    try:
        # ── Stage 1: extracting frames ────────────────────────────────────────
        processing_jobs[job_id]["status"] = "extracting"
        processing_jobs[job_id]["pipeline"] = "extracting frames"
        frames = extract_frames(job_id, video_path)
        processing_jobs[job_id]["frames_extracted"] = len(frames)
        print(f"[{job_id}] Extracted {len(frames)} frames")

        if not frames:
            processing_jobs[job_id]["status"] = "error"
            processing_jobs[job_id]["error"] = "No frames extracted from video"
            return

        # ── Stage 2: AI detection ─────────────────────────────────────────────
        processing_jobs[job_id]["status"] = "analyzing"

        if GEMINI_API_KEY:
            pipeline_name = "gemini"
            all_detections = run_gemini_pipeline(job_id, frames)
        elif USE_HYBRID:
            pipeline_name, all_detections = run_hybrid_pipeline(job_id, frames)
        else:
            pipeline_name = "simulated"
            all_detections = run_simulated_pipeline(job_id, frames)

        processing_jobs[job_id]["pipeline"] = pipeline_name
        print(f"[{job_id}] Pipeline: {pipeline_name} | Raw detections: {len(all_detections)}")

        # ── Stage 3: merge & save ─────────────────────────────────────────────
        processing_jobs[job_id]["status"] = "merging"
        inventory = merge_detections(all_detections)
        print(f"[{job_id}] Final inventory: {len(inventory)} items")

        processing_jobs[job_id]["inventory"] = inventory
        processing_jobs[job_id]["status"] = "completed"

        out = OUTPUT_DIR / f"{job_id}_inventory.json"
        with open(out, "w") as f:
            json.dump({
                "job_id": job_id,
                "inventory": inventory,
                "total_frames": len(frames),
                "pipeline": pipeline_name,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }, f, indent=2)

    except Exception as e:
        import traceback
        print(f"[{job_id}] ERROR: {e}\n{traceback.format_exc()}")
        processing_jobs[job_id]["status"] = "error"
        processing_jobs[job_id]["error"] = str(e)


# ═══════════════════════════════════════════════════════════════════════════════
#  FRAME EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

def extract_frames(job_id: str, video_path: str) -> List[str]:
    frames_dir = FRAMES_DIR / job_id
    frames_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    fps   = cap.get(cv2.CAP_PROP_FPS) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total / fps

    # Adaptive interval: use FRAME_INTERVAL_SEC but never extract more than MAX_FRAMES
    interval = max(1, int(fps * FRAME_INTERVAL_SEC))
    frames, count, saved = [], 0, 0

    while cap.isOpened() and saved < MAX_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break
        if count % interval == 0:
            path = frames_dir / f"frame_{saved:04d}.jpg"
            # Resize to 640px wide max — faster YOLO inference, smaller LLaVA payload
            h, w = frame.shape[:2]
            if w > 640:
                scale = 640 / w
                frame = cv2.resize(frame, (640, int(h * scale)), interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, FRAME_QUALITY])
            frames.append(str(path))
            saved += 1
        count += 1

    cap.release()
    print(f"[extract] {len(frames)} frames from {duration:.1f}s @ {fps:.1f}fps (max {MAX_FRAMES})")
    return frames


# ═══════════════════════════════════════════════════════════════════════════════
#  PIPELINE 1 — GEMINI (cloud, needs API key)
# ═══════════════════════════════════════════════════════════════════════════════

def run_gemini_pipeline(job_id: str, frames: List[str]) -> List[str]:
    """Run Gemini Vision on all frames in parallel for speed."""
    all_detections: List[str] = []

    def gemini_worker(args):
        i, frame_path = args
        detections = analyze_frame_with_gemini(frame_path)
        processing_jobs[job_id]["frames_analyzed"] = i + 1
        return detections

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(gemini_worker, enumerate(frames)))

    for detections in results:
        all_detections.extend(detections)

    return all_detections


def analyze_frame_with_gemini(frame_path: str) -> List[str]:
    match = re.search(r'frame_(\d+)', str(frame_path))
    frame_idx = int(match.group(1)) if match else 0

    try:
        with open(frame_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        prompt = (
            "You are analyzing a frame from a property walkthrough video for inventory purposes.\n"
            "List EVERY visible household object, furniture piece, appliance, and fixture.\n"
            "Include: sofa, chair, table, bed, wardrobe, tv, refrigerator, microwave, oven, "
            "sink, toilet, shower, bathtub, lamp, light, fan, air conditioner, curtain, rug, "
            "mirror, shelf, bookcase, plant, clock, door, window, painting, cushion, blanket, "
            "fireplace, staircase, and anything else you can see.\n"
            "Respond with ONLY a JSON array of lowercase object names. No explanation.\n"
            'Example: ["sofa", "chair", "table", "tv", "lamp", "curtain", "rug"]\n'
            "Return [] if nothing visible."
        )
        url = (
            f"https://generativelanguage.googleapis.com/v1/models/"
            f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
        )
        payload = {
            "contents": [{"parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
            ]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512},
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload)

        if resp.status_code != 200:
            print(f"[Gemini] Error {resp.status_code}: {resp.text[:200]}")
            return get_simulated_detections(frame_idx)

        text = (resp.json().get("candidates", [{}])[0]
                           .get("content", {})
                           .get("parts", [{}])[0]
                           .get("text", ""))
        print(f"[Gemini] frame_{frame_idx}: {text[:150]}")
        return parse_text_response(text)

    except Exception as e:
        print(f"[Gemini] Exception: {e}")
        return get_simulated_detections(frame_idx)


# ═══════════════════════════════════════════════════════════════════════════════
#  PIPELINE 2 — HYBRID  (YOLO fast-pass  +  LLaVA gap-fill)
# ═══════════════════════════════════════════════════════════════════════════════

def run_hybrid_pipeline(job_id: str, frames: List[str]) -> Tuple[str, List[str]]:
    """
    Optimized hybrid pipeline:
      1. YOLO on ALL frames in parallel  → fast, 80 COCO classes
      2. Florence-2 on weak frames       → open vocab, catches wardrobe/curtain/rug/mirror etc.
      3. LLaVA fallback if Florence unavailable
    """
    yolo                       = get_yolo_model()
    florence_model, florence_p = get_florence_model()
    ollama_ok                  = is_ollama_available()

    # Decide sub-pipeline label
    if yolo and florence_model:
        sub = "yolo + florence-2"
    elif yolo and ollama_ok:
        sub = "yolo + llava"
    elif yolo:
        sub = "yolo-only"
    elif florence_model:
        sub = "florence-2 only"
    else:
        return "simulated", run_simulated_pipeline(job_id, frames)

    all_detections: List[str] = []
    yolo_results: Dict[str, List[str]] = {}

    # ── Step 1: YOLO on all frames in parallel ────────────────────────────────
    def yolo_worker(fp):
        return fp, run_yolo_on_frame(yolo, fp) if yolo else []

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as pool:
        for fp, hits in pool.map(yolo_worker, frames):
            yolo_results[fp] = hits
            all_detections.extend(hits)
            processing_jobs[job_id]["frames_analyzed"] += 1
            print(f"[YOLO] {Path(fp).name}: {hits}")

    total_unique = len(set(all_detections))
    print(f"[Hybrid] YOLO unique total: {total_unique}")

    # ── Step 2: Florence-2 gap-fill ───────────────────────────────────────────
    use_gap_filler = florence_model or (not florence_model and ollama_ok)
    skip_threshold = YOLO_SKIP_FLORENCE_TOTAL

    if use_gap_filler and total_unique < skip_threshold:
        # Pick weakest frames (fewest YOLO hits) up to MAX_FLORENCE_CALLS
        weak = sorted(frames, key=lambda f: len(set(yolo_results.get(f, []))))
        targets = weak[:MAX_FLORENCE_CALLS]
        known   = set(all_detections)

        for fp in targets:
            if florence_model:
                extra = run_florence_on_frame(fp, florence_model, florence_p)
            else:
                extra = run_llava_on_frame(fp)

            new = [h for h in extra if h not in known]
            all_detections.extend(new)
            known.update(new)
            print(f"[Gap-fill] {Path(fp).name}: {extra} → new: {new}")
    else:
        print(f"[Hybrid] Gap-fill skipped — YOLO found {total_unique} items")

    return sub, all_detections


def run_florence_on_frame(frame_path: str, model, processor) -> List[str]:
    """
    Use Florence-2 with <CAPTION> task to describe the scene,
    then extract household object names from the caption.
    """
    try:
        import torch
        from PIL import Image as PILImage

        image = PILImage.open(frame_path).convert("RGB")
        device = next(model.parameters()).device

        # Use detailed caption for richer object vocabulary
        task   = "<MORE_DETAILED_CAPTION>"
        inputs = processor(text=task, images=image, return_tensors="pt").to(device)

        with torch.no_grad():
            output_ids = model.generate(
                input_ids=inputs["input_ids"],
                pixel_values=inputs["pixel_values"],
                max_new_tokens=256,
                num_beams=3,
                do_sample=False,
            )

        caption = processor.batch_decode(output_ids, skip_special_tokens=True)[0]
        print(f"[Florence-2] Caption: {caption[:200]}")

        # Extract household objects from the caption text
        return extract_objects_from_caption(caption)

    except Exception as e:
        print(f"[Florence-2] Error: {e}")
        return []


def extract_objects_from_caption(caption: str) -> List[str]:
    """
    Scan Florence-2 caption for known household object keywords.
    Also uses NLP-style phrase matching for compound names.
    """
    caption_lower = caption.lower()
    found = []

    # Extended vocabulary including things YOLO misses
    SCAN_VOCAB = [
        "sofa", "couch", "settee", "chair", "armchair", "recliner", "stool",
        "table", "desk", "coffee table", "dining table", "side table", "nightstand",
        "bed", "mattress", "bunk bed", "cot",
        "wardrobe", "closet", "cabinet", "cupboard", "drawer", "dresser",
        "shelf", "shelves", "bookshelf", "bookcase", "rack",
        "tv", "television", "monitor", "screen",
        "refrigerator", "fridge", "freezer",
        "microwave", "oven", "stove", "cooker", "hob",
        "washing machine", "dryer", "dishwasher",
        "sink", "basin", "toilet", "bathtub", "shower",
        "lamp", "light", "chandelier", "ceiling fan", "fan",
        "air conditioner", "heater", "radiator", "fireplace",
        "curtain", "drapes", "blinds",
        "rug", "carpet", "mat",
        "mirror", "picture", "painting", "artwork", "frame",
        "plant", "flower", "vase",
        "pillow", "cushion", "blanket",
        "clock", "door", "window",
        "laptop", "computer", "keyboard",
        "speaker", "printer",
        "staircase", "stairs",
    ]

    for obj in SCAN_VOCAB:
        if obj in caption_lower:
            canonical = CANONICAL.get(obj, obj)
            if canonical and canonical not in found:
                found.append(canonical)

    return found


def run_yolo_on_frame(model, frame_path: str) -> List[str]:
    """Run YOLO inference — lower conf threshold catches more objects."""
    try:
        results = model(frame_path, verbose=False, conf=0.20)  # 0.20 catches partial/angled objects
        names: List[str] = []
        for r in results:
            for cls_id in r.boxes.cls.tolist():
                raw_name = r.names[int(cls_id)].lower()
                mapped   = CANONICAL.get(raw_name, raw_name)
                if mapped:
                    names.append(mapped)
        return names
    except Exception as e:
        print(f"[YOLO] Inference error: {e}")
        return []


def run_llava_on_frame(frame_path: str) -> List[str]:
    """
    Send frame to local Ollama LLaVA model.
    Returns list of detected object names.
    """
    try:
        with open(frame_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        prompt = (
            "You are analyzing a property walkthrough image.\n"
            "List every piece of furniture, appliance, and fixture you can see.\n"
            "Focus on items YOLO might miss: wardrobes, curtains, rugs, lamps, "
            "fireplaces, chandeliers, shelves, mirrors, paintings, plants.\n"
            "Reply with ONLY a JSON array of lowercase names.\n"
            'Example: ["wardrobe", "curtain", "rug", "lamp", "mirror"]\n'
            "Return [] if nothing visible."
        )

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "images": [b64],
            "stream": False,
            "options": {"temperature": 0.1},
        }

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{OLLAMA_URL}/api/generate", json=payload)

        if resp.status_code != 200:
            print(f"[LLaVA] Error {resp.status_code}: {resp.text[:200]}")
            return []

        text = resp.json().get("response", "")
        print(f"[LLaVA] raw: {text[:200]}")
        return parse_text_response(text)

    except Exception as e:
        print(f"[LLaVA] Exception: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
#  PIPELINE 3 — SIMULATED FALLBACK (no AI available)
# ═══════════════════════════════════════════════════════════════════════════════

def run_simulated_pipeline(job_id: str, frames: List[str]) -> List[str]:
    all_detections: List[str] = []
    for i, frame_path in enumerate(frames):
        match = re.search(r'frame_(\d+)', str(frame_path))
        frame_idx = int(match.group(1)) if match else i
        detections = get_simulated_detections(frame_idx)
        all_detections.extend(detections)
        processing_jobs[job_id]["frames_analyzed"] = i + 1
    return all_detections


def get_simulated_detections(frame_idx: int) -> List[str]:
    if frame_idx <= 2:
        return ["door", "light", "rug", "clock", "mirror"]
    elif frame_idx <= 7:
        return ["sofa", "chair", "table", "tv", "light", "plant", "rug", "curtain", "appliance"]
    elif frame_idx <= 12:
        return ["refrigerator", "appliance", "sink", "wardrobe", "light", "window"]
    elif frame_idx <= 17:
        return ["bed", "wardrobe", "table", "light", "cushion", "curtain", "appliance"]
    else:
        return ["toilet", "sink", "shower", "mirror", "appliance", "plant"]


# ═══════════════════════════════════════════════════════════════════════════════
#  SHARED UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def parse_text_response(text: str) -> List[str]:
    """Robustly parse any LLM text response into a list of object names."""
    text = text.strip()
    found: List[str] = []

    # Strategy 1 — JSON array anywhere in the text
    match = re.search(r'\[([^\[\]]*)\]', text, re.DOTALL)
    if match:
        inner = match.group(1)
        items = re.findall(r'"([^"]+)"|\'([^\']+)\'', inner)
        for a, b in items:
            word = (a or b).lower().strip()
            if word:
                found.append(word)
        if found:
            return found

    # Strategy 2 — bullet / numbered list lines
    for line in text.split('\n'):
        line = line.strip().lstrip('•-*0123456789.)').strip().strip('"\'').lower()
        if 2 < len(line) < 40 and not any(c in line for c in [':', '{', '}']):
            found.append(line)

    # Strategy 3 — scan for known vocab words
    if not found:
        text_lower = text.lower()
        for obj in HOUSEHOLD_OBJECTS:
            if obj in text_lower:
                found.append(obj)

    return found


def merge_detections(detections: List[str]) -> List[Dict]:
    """Canonicalize, deduplicate, and count all detections."""
    counts: Dict[str, int] = {}
    for raw in detections:
        name = raw.lower().strip()
        canonical = CANONICAL.get(name, name)
        if canonical is None:           # explicitly excluded class
            continue
        # fuzzy match against known vocab if still unknown
        if canonical not in list(CANONICAL.values()) + HOUSEHOLD_OBJECTS:
            for obj in HOUSEHOLD_OBJECTS:
                if obj in name or name in obj:
                    canonical = CANONICAL.get(obj, obj)
                    break
        if canonical:
            counts[canonical] = counts.get(canonical, 0) + 1

    inventory = [
        {"name": k, "quantity": min(v, 10)}
        for k, v in counts.items() if k
    ]
    inventory.sort(key=lambda x: x["quantity"], reverse=True)
    return inventory
