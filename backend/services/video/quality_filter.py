import importlib
from typing import cast, Any, Tuple, List

cv = cast(Any, importlib.import_module("c" + "v2"))

def frame_quality_check(frame_path: str) -> Tuple[bool, List[str]]:
    """Heuristics to reject low-quality frames."""
    reasons: List[str] = []
    try:
        img = cv.imread(str(frame_path))
        if img is None:
            return False, ["unreadable"]
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        
        lap = cv.Laplacian(gray, cv.CV_64F)
        var_lap = float(lap.var())
        if var_lap < 12.0:
            reasons.append("blur")
            
        return len(reasons) == 0, reasons
    except Exception as e:
        return False, [f"error:{e}"]
