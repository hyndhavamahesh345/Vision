import json
import time
from pathlib import Path
from celery import shared_task
from sqlalchemy.orm import Session

from config import logger, FRAMES_DIR, USE_HYBRID, OUTPUT_DIR, FAST_MODE
from worker.redis import celery_app
from storage.minio import download_video
from db.postgres import SessionLocal, Job, Inventory, Detection

from services.video.frame_extractor import extract_frames
from detection_engine.router import route_frame
from aggregator.aggregator import aggregate_detections
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

def process_video_sync(job_id: str, object_name: str):
    logger.info("[%s] Starting process_video for: %s", job_id, object_name)
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

        all_detections = []
        for idx, frame_path in enumerate(frames):
            # Route frame through YOLO-World
            frame_detections = route_frame(frame_path, "custom-yolo", job_id, idx)
            all_detections.extend(frame_detections)
            if FAST_MODE or len(frames) <= 10 or idx % 5 == 0:
                update_job_status(db, job_id, "analyzing", frames_analyzed=idx+1)

        update_job_status(db, job_id, "merging", pipeline="yolo-world", frames_analyzed=len(frames))
        
        agg_result = aggregate_detections(all_detections)
        inventory = agg_result["inventory"]
        validation_data = agg_result.get("validation_data", {})
        
        if validation_data:
            logger.info("[%s] Tracking Validation Data: %s", job_id, validation_data)

        # Save to database
        for item in inventory:
            name = item.get("name", "")
            count = item.get("quantity", 0)
            room = "Home"
            
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

@celery_app.task(bind=True)
def process_video_task(self, job_id: str, object_name: str):
    process_video_sync(job_id, object_name)

def process_frames_sync(job_id: str):
    logger.info("[%s] Starting process_frames for pre-extracted frames", job_id)
    db = SessionLocal()
    
    try:
        job_frames_dir = FRAMES_DIR / job_id
        if not job_frames_dir.exists():
            raise FileNotFoundError(f"Frames directory not found: {job_frames_dir}")
            
        frames = sorted(list(job_frames_dir.glob("*.jpg"))) + sorted(list(job_frames_dir.glob("*.jpeg")))
        
        update_job_status(db, job_id, "extracting", frames_extracted=len(frames))

        if not frames:
            update_job_status(db, job_id, "error", error="No frames found")
            return

        update_job_status(db, job_id, "analyzing")

        all_detections = []
        for idx, frame_path in enumerate(frames):
            # Route frame through YOLO-World
            frame_detections = route_frame(str(frame_path), "custom-yolo", job_id, idx)
            all_detections.extend(frame_detections)
            if FAST_MODE or len(frames) <= 10 or idx % 5 == 0:
                update_job_status(db, job_id, "analyzing", frames_analyzed=idx+1)

        update_job_status(db, job_id, "merging", pipeline="yolo-world", frames_analyzed=len(frames))
        
        agg_result = aggregate_detections(all_detections)
        inventory = agg_result["inventory"]
        validation_data = agg_result.get("validation_data", {})
        
        if validation_data:
            logger.info("[%s] Tracking Validation Data: %s", job_id, validation_data)

        # Save to database
        for item in inventory:
            name = item.get("name", "")
            count = item.get("quantity", 0)
            room = "Home"
            
            db_inv = Inventory(job_id=job_id, room=room, object=name, count=count)
            db.add(db_inv)

        update_job_status(db, job_id, "completed")
        db.commit()
        
    except Exception as e:
        logger.exception("[%s] ERROR in Celery task: %s", job_id, e)
        update_job_status(db, job_id, "error", error=str(e))
    finally:
        db.close()

@celery_app.task(bind=True)
def process_frames_task(self, job_id: str):
    process_frames_sync(job_id)

