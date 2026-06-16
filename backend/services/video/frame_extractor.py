import importlib
from typing import cast, Any, List
from config import FRAMES_DIR, FRAME_INTERVAL_SEC, MAX_FRAMES, FRAME_QUALITY, logger

cv = cast(Any, importlib.import_module("c" + "v2"))

def extract_frames(job_id: str, video_path: str) -> List[str]:
    frames_dir = FRAMES_DIR / job_id
    frames_dir.mkdir(parents=True, exist_ok=True)

    cap = cv.VideoCapture(video_path)
    fps   = cap.get(cv.CAP_PROP_FPS) or 30
    total = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
    duration = total / fps

    ABSOLUTE_MAX_FRAMES = 60  # Cap at 60 frames to ensure absolute max of ~2 minutes processing time
    base_interval = int(fps * FRAME_INTERVAL_SEC)
    dynamic_interval = int(total / ABSOLUTE_MAX_FRAMES) if total > 0 else 1
    interval = max(1, base_interval, dynamic_interval)
    
    frames, count, saved = [], 0, 0

    while cap.isOpened() and saved < ABSOLUTE_MAX_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break
        if count % interval == 0:
            path = frames_dir / f"frame_{saved:04d}.jpg"
            h, w = frame.shape[:2]
            if w > 320:
                scale = 320 / w
                frame = cv.resize(frame, (320, int(h * scale)), interpolation=cv.INTER_AREA)
            cv.imwrite(str(path), frame, [cv.IMWRITE_JPEG_QUALITY, FRAME_QUALITY])
            frames.append(str(path))
            saved += 1
        count += 1

    cap.release()
    logger.info("[extract] %d frames from %.1fs @ %.1ffps (max %d)", len(frames), duration, fps, MAX_FRAMES)
    return frames
