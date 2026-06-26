import sys
from pathlib import Path

# Add backend directory to sys.path to resolve imports properly
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from worker.tasks import process_video_sync, process_frames_sync

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python process_job.py <video|frames> <job_id> [object_name]")
        sys.exit(1)
        
    task_type = sys.argv[1]
    job_id = sys.argv[2]
    
    if task_type == "video":
        if len(sys.argv) < 4:
            print("Usage: python process_job.py video <job_id> <object_name>")
            sys.exit(1)
        object_name = sys.argv[3]
        process_video_sync(job_id, object_name)
    elif task_type == "frames":
        process_frames_sync(job_id)
    else:
        print(f"Unknown task type: {task_type}")
        sys.exit(1)
