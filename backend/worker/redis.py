import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# If REDIS_URL is not connectable or if we want local mode, run eager
USE_EAGER_CELERY = os.getenv("USE_EAGER_CELERY", "true").lower() == "true"

celery_app = Celery(
    "visionvault_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Worker optimizations for CV
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

if USE_EAGER_CELERY:
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True
    )
    from config import logger
    logger.info("[Celery] Running in eager (synchronous, in-process) mode. Redis not required.")

# Import tasks so Celery discovers them
import worker.tasks
