import cv2
from pathlib import Path
import os
import shutil

videos_dir = Path(r"C:\Users\SOBHASREE SADU\OneDrive\Desktop\New folder (3)\videos")
output_dir = Path("dataset/images/train")

if not videos_dir.exists():
    print(f"Directory not found: {videos_dir}")
    exit(1)

# Ensure output directory exists (we don't delete to keep existing frames if any, but let's just keep adding to it)
output_dir.mkdir(parents=True, exist_ok=True)

video_files = list(videos_dir.glob("*.mp4"))
print(f"Found {len(video_files)} videos.")

total_frames = 0
for idx, video_path in enumerate(video_files):
    print(f"Processing video {idx+1}/{len(video_files)}: {video_path.name}")
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Failed to open {video_path.name}")
        continue
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30 # fallback
    
    frame_interval = int(fps * 1) # 1 frame per second
    
    frame_count = 0
    extracted = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_count % frame_interval == 0:
            out_path = output_dir / f"vid_{idx}_f{frame_count}.jpg"
            cv2.imwrite(str(out_path), frame)
            extracted += 1
            total_frames += 1
            
        frame_count += 1
        
    cap.release()
    print(f"  Extracted {extracted} frames from {video_path.name}")

print(f"Done! Extracted a total of {total_frames} frames from all videos.")
