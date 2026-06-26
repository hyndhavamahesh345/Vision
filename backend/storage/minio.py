import os
import io
import shutil
from pathlib import Path
from minio import Minio
from config import logger

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "password123")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Determine if we should use local storage fallback
USE_LOCAL_STORAGE = os.getenv("USE_LOCAL_STORAGE", "true").lower() == "true"

minio_client = None
if not USE_LOCAL_STORAGE:
    try:
        minio_client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
    except Exception as e:
        logger.warning("[MinIO] Failed to initialize client, forcing local storage fallback. Error: %s", e)
        USE_LOCAL_STORAGE = True

def init_buckets():
    if USE_LOCAL_STORAGE:
        logger.info("[Local Storage] Initializing local storage folders instead of MinIO")
        for bucket in ["videos", "thumbnails", "reports"]:
            Path(f"local_storage/{bucket}").mkdir(parents=True, exist_ok=True)
        return

    buckets = ["videos", "thumbnails", "reports"]
    for bucket in buckets:
        try:
            if not minio_client.bucket_exists(bucket):
                minio_client.make_bucket(bucket)
                logger.info("[MinIO] Created bucket '%s'", bucket)
        except Exception as e:
            logger.error("[MinIO] Failed to create bucket '%s': %s", bucket, e)

def upload_video(job_id: str, file_path: str, ext: str) -> str:
    bucket = "videos"
    object_name = f"{job_id}{ext}"
    if USE_LOCAL_STORAGE:
        dest = Path(f"local_storage/{bucket}/{object_name}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(file_path, dest)
        logger.info("[Local Storage] Uploaded %s to local_storage/%s", object_name, bucket)
        return object_name

    try:
        minio_client.fput_object(bucket, object_name, file_path)
        logger.info("[MinIO] Uploaded %s to bucket %s", object_name, bucket)
        return object_name
    except Exception as e:
        logger.error("[MinIO] Upload failed for %s: %s", object_name, e)
        raise

def download_video(object_name: str, download_path: str):
    bucket = "videos"
    if USE_LOCAL_STORAGE:
        src = Path(f"local_storage/{bucket}/{object_name}")
        if src.exists():
            shutil.copy(src, download_path)
            logger.info("[Local Storage] Downloaded %s to %s", object_name, download_path)
            return
        else:
            raise FileNotFoundError(f"Local storage file not found: {src}")

    try:
        minio_client.fget_object(bucket, object_name, download_path)
        logger.info("[MinIO] Downloaded %s to %s", object_name, download_path)
    except Exception as e:
        logger.error("[MinIO] Download failed for %s: %s", object_name, e)
        raise
