import cv2
import numpy as np

# Video configuration
width, height = 640, 480
fps = 30
duration = 20  # seconds
num_frames = duration * fps
out_path = 'sample_walkthrough.mp4'

# Create a VideoWriter object
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

# Room names and durations (in frames)
rooms = [
    ("Entrance & Hallway", 4 * fps, (50, 50, 120)),      # Reddish-brown
    ("Living Room", 4 * fps, (120, 50, 50)),            # Bluish
    ("Kitchen & Dining", 4 * fps, (50, 120, 50)),       # Greenish
    ("Master Bedroom", 4 * fps, (120, 50, 120)),        # Purpleish
    ("Bathroom & Balcony", 4 * fps, (80, 80, 80))       # Greyish
]

current_frame = 0
for room_name, room_frames, base_color in rooms:
    for f in range(room_frames):
        # Create gradient background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            factor = y / height
            color = [
                int(base_color[0] * (1 - factor * 0.5)),
                int(base_color[1] * (1 - factor * 0.5)),
                int(base_color[2] * (1 - factor * 0.5))
            ]
            frame[y, :] = color
        
        # Add decorative grid overlay (very subtle grey)
        grid_color = (60, 60, 60)
        for grid_y in range(0, height, 40):
            cv2.line(frame, (0, grid_y), (width, grid_y), grid_color, 1)
        for grid_x in range(0, width, 40):
            cv2.line(frame, (grid_x, 0), (grid_x, height), grid_color, 1)
        
        # Draw room text
        cv2.putText(frame, "VisionVault — AI Property Scan", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Active Zone: {room_name}", (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, "Scanning environment...", (30, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 255, 200), 2, cv2.LINE_AA)
        
        # Status blinking indicator
        if (current_frame // 15) % 2 == 0:
            cv2.circle(frame, (width - 50, 50), 12, (0, 0, 255), -1)
            cv2.putText(frame, "REC", (width - 110, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
        else:
            cv2.circle(frame, (width - 50, 50), 12, (30, 30, 100), -1)
            cv2.putText(frame, "REC", (width - 110, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 100), 2, cv2.LINE_AA)
            
        # Draw frame number / scan indicator
        progress = int((current_frame / num_frames) * 100)
        cv2.rectangle(frame, (30, height - 60), (width - 30, height - 40), (40, 40, 40), -1)
        cv2.rectangle(frame, (30, height - 60), (30 + int((width - 60) * (progress / 100)), height - 40), (0, 220, 0), -1)
        cv2.putText(frame, f"Analysis Progress: {progress}%", (30, height - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        out.write(frame)
        current_frame += 1

out.release()
print("Successfully generated sample_walkthrough.mp4!")
