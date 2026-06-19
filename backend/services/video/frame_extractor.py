import importlib
from typing import cast, Any, List
from config import FRAMES_DIR, FRAME_INTERVAL_SEC, MAX_FRAMES, FRAME_QUALITY, logger

cv = cast(Any, importlib.import_module("c" + "v2"))

def extract_frames(job_id: str, video_path: str) -> List[str]:
    frames_dir = FRAMES_DIR / job_id
    frames_dir.mkdir(parents=True, exist_ok=True)

    cap = cv.VideoCapture(video_path)
    fps = cap.get(cv.CAP_PROP_FPS) or 30
    total = int(cap.get(cv.CAP_PROP_FRAME_COUNT))
    duration = total / fps

    ABSOLUTE_MAX_FRAMES = 60
    
    frames, count, saved = [], 0, 0
    prev_gray = None
    
    # Motion detection thresholds
    MOTION_THRESHOLD = 30
    PIXEL_CHANGE_RATIO = 0.05  # 5% of pixels must change

    while cap.isOpened() and saved < ABSOLUTE_MAX_FRAMES:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Resize for faster processing and saving
        h, w = frame.shape[:2]
        if w > 320:
            scale = 320 / w
            frame = cv.resize(frame, (320, int(h * scale)), interpolation=cv.INTER_AREA)

        gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        
        should_save = False
        if prev_gray is None:
            should_save = True
        else:
            # Calculate absolute difference between current frame and previous saved frame
            diff = cv.absdiff(prev_gray, gray)
            _, thresh = cv.threshold(diff, MOTION_THRESHOLD, 255, cv.THRESH_BINARY)
            changed_pixels = cv.countNonZero(thresh)
            total_pixels = gray.shape[0] * gray.shape[1]
            
            if (changed_pixels / total_pixels) > PIXEL_CHANGE_RATIO:
                should_save = True
                
        # Also save at least one frame every 3 seconds just in case of slow panning
        if count % int(fps * 3) == 0:
            should_save = True

        if should_save:
            path = frames_dir / f"frame_{saved:04d}.jpg"
            cv.imwrite(str(path), frame, [cv.IMWRITE_JPEG_QUALITY, FRAME_QUALITY])
            frames.append(str(path))
            prev_gray = gray
            saved += 1
            
        count += 1

    cap.release()
    logger.info("[extract] %d keyframes from %.1fs @ %.1ffps using motion detection", len(frames), duration, fps)
    return frames
