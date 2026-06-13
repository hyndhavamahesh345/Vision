import cv2
import os
from pathlib import Path

video_path = r"C:\Users\SOBHASREE SADU\OneDrive\Desktop\New folder (3)\videos\WhatsApp Video 2026-06-12 at 19.29.32.mp4"
output_dir = Path("dataset/images/train")
output_dir.mkdir(parents=True, exist_ok=True)

cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
if fps <= 0: fps = 30

# Extract 1 frame per second to ensure diverse shots
frame_interval = int(fps * 1.0) 

frame_idx = 0
saved_count = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    
    if frame_idx % frame_interval == 0:
        cv2.imwrite(str(output_dir / f"frame_{saved_count}.jpg"), frame)
        saved_count += 1
    
    frame_idx += 1

cap.release()
print(f"Extracted {saved_count} frames to {output_dir}")
