import threading
from typing import Dict, Any

# Global state for jobs
processing_jobs: Dict[str, Dict[str, Any]] = {}

# Threading locks for safe lazy model initialization
_yolo_lock = threading.Lock()
_groundingdino_lock = threading.Lock()
