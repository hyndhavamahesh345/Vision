import os
import io
from minio import Minio
from config import logger

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "password123")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE
)

def init_buckets():
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
    try:
        minio_client.fput_object(bucket, object_name, file_path)
        logger.info("[MinIO] Uploaded %s to bucket %s", object_name, bucket)
        return object_name
    except Exception as e:
        logger.error("[MinIO] Upload failed for %s: %s", object_name, e)
        raise

def download_video(object_name: str, download_path: str):
    bucket = "videos"
    try:
        minio_client.fget_object(bucket, object_name, download_path)
        logger.info("[MinIO] Downloaded %s to %s", object_name, download_path)
    except Exception as e:
        logger.error("[MinIO] Download failed for %s: %s", object_name, e)
        raise
