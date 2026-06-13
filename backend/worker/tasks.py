import json
import time
from pathlib import Path
from celery import shared_task
from sqlalchemy.orm import Session

from config import logger, FRAMES_DIR, USE_HYBRID, OUTPUT_DIR
from worker.redis import celery_app
from storage.minio import download_video
from db.postgres import SessionLocal, Job, Inventory, Detection

from services.video.frame_extractor import extract_frames
from services.fusion.fusion_engine import run_hybrid_pipeline, run_simulated_pipeline
from services.inventory.builder import merge_detections
from services.room.classifier import get_local_room_assignment

def update_job_status(db: Session, job_id: str, status: str, pipeline: str = None, error: str = None, frames_extracted: int = 0, frames_analyzed: int = 0):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job:
        job.status = status
        if pipeline: job.pipeline = pipeline
        if error: job.error = error
        if frames_extracted: job.frames_extracted = frames_extracted
        if frames_analyzed: job.frames_analyzed = frames_analyzed
        db.commit()

@celery_app.task(bind=True)
def process_video_task(self, job_id: str, object_name: str):
    logger.info("[%s] Starting Celery task for video: %s", job_id, object_name)
    db = SessionLocal()
    
    # Download video from MinIO to local temp space
    temp_dir = Path("/tmp/visionvault_workers") if Path("/tmp").exists() else FRAMES_DIR.parent / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    local_video_path = str(temp_dir / object_name)
    
    try:
        update_job_status(db, job_id, "downloading")
        download_video(object_name, local_video_path)

        update_job_status(db, job_id, "extracting", pipeline="extracting frames")
        frames = extract_frames(job_id, local_video_path)
        update_job_status(db, job_id, "extracting", frames_extracted=len(frames))

        if not frames:
            update_job_status(db, job_id, "error", error="No frames extracted")
            return

        update_job_status(db, job_id, "analyzing")

        if USE_HYBRID:
            pipeline_name, all_detections = run_hybrid_pipeline(job_id, local_video_path, frames)
            flat_count = sum(len(f) for f in all_detections)
            if flat_count == 0:
                pipeline_name = "simulated fallback"
                all_detections = run_simulated_pipeline(job_id, frames)
        else:
            pipeline_name = "simulated"
            all_detections = run_simulated_pipeline(job_id, frames)

        update_job_status(db, job_id, "merging", pipeline=pipeline_name, frames_analyzed=len(frames))
        
        inventory = merge_detections(all_detections)

        # Save to database
        for item in inventory:
            name = item.get("name", "")
            count = item.get("quantity", 0)
            room = get_local_room_assignment(name)
            
            db_inv = Inventory(job_id=job_id, room=room, object=name, count=count)
            db.add(db_inv)

        update_job_status(db, job_id, "completed")
        db.commit()
        
    except Exception as e:
        logger.exception("[%s] ERROR in Celery task: %s", job_id, e)
        update_job_status(db, job_id, "error", error=str(e))
    finally:
        db.close()
        # Clean up local video file
        if Path(local_video_path).exists():
            Path(local_video_path).unlink()
