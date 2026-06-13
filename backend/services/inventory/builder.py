from typing import Optional, List, Dict

# ── Household Vocabulary ──────────────────────────────────────────────────────
HOUSEHOLD_OBJECTS = [
    "sofa", "couch", "chair", "armchair", "table", "dining table", "coffee table",
    "desk", "tv", "television", "monitor", "bed", "mattress", "wardrobe", "closet",
    "cabinet", "cupboard", "refrigerator", "fridge", "fan", "ceiling fan", "light",
    "lamp", "chandelier", "door", "window", "shelf", "bookshelf", "rack",
    "clock", "rug", "carpet", "curtain", "blinds", "plant", "potted plant",
    "washing machine", "microwave", "oven", "stove", "sink", "toilet", "bathtub",
    "shower", "mirror", "picture frame", "painting", "pillow", "cushion",
    "blanket", "air conditioner", "heater", "water heater", "geyser", "fireplace", "staircase",
    "drawer", "nightstand", "bench", "ottoman", "bookcase", "kettle",
    "toaster", "dishwasher", "dryer", "iron", "vacuum", "printer",
    "speaker", "router", "phone", "laptop", "computer", "power plugs", "light switch",
    "projector", "chimney", "ac"
]

CANONICAL = {
    "couch": "sofa", "settee": "sofa",
    "armchair": "armchair", "recliner": "chair", "stool": "stool",
    "dining table": "dining table", "coffee table": "coffee table", "desk": "desk",
    "side table": "table", "end table": "table", "nightstand": "nightstand",
    "bedside table": "nightstand",
    "television": "tv", "monitor": "tv", "screen": "tv",
    "mattress": "bed", "bunk bed": "bed",
    "closet": "closet", "cupboard": "cupboard", "cabinet": "cabinet",
    "drawer": "drawer", "chest of drawers": "drawer",
    "fridge": "refrigerator", "freezer": "refrigerator",
    "ceiling fan": "ceiling fan", "table fan": "fan", "pedestal fan": "fan",
    "lamp": "lamp", "chandelier": "chandelier", "ceiling light": "light",
    "wall light": "light", "bulb": "light", "light bulb": "light", "light fixture": "light",
    "bookshelf": "bookshelf", "bookcase": "bookshelf", "rack": "shelf",
    "carpet": "rug", "mat": "rug",
    "blinds": "blinds", "drapes": "curtain", "window blind": "blinds", "window shade": "blinds", "curtain rod": "curtain",
    "potted plant": "plant", "indoor plant": "plant", "flower": "plant",
    "washing machine": "washing machine", "microwave": "microwave",
    "oven": "oven", "stove": "stove", "kettle": "kettle",
    "toaster": "toaster", "dishwasher": "dishwasher", "dryer": "dryer",
    "iron": "iron", "vacuum": "vacuum",
    "ottoman": "ottoman", "bench": "bench",
    "picture frame": "picture frame", "painting": "painting",
    "pillow": "pillow",
    "air conditioner": "air conditioner", "heater": "heater", "water heater": "geyser", "geyser": "geyser", "ac": "air conditioner",
    "power plugs and sockets": "power plugs", "power outlet": "power plugs",
    "power plug": "power plugs", "socket": "power plugs", "electrical outlet": "power plugs",
    "outlet": "power plugs", "plug": "power plugs",
    "light switch": "light switch", "switch": "light switch",
    "door handle": "door", "door knob": "door", "door frame": "door", "doorframe": "door",
    "window frame": "window",
    "sink faucet": "sink", "faucet": "sink", "tap": "sink", "kitchen sink": "sink", "bathroom sink": "sink",
    "projector": "projector", "chimney": "chimney",
}

def normalize_object_name(raw_name: str) -> Optional[str]:
    if raw_name is None:
        return None
    name = str(raw_name).lower().strip()

    if name in CANONICAL:
        return CANONICAL[name]

    if name in HOUSEHOLD_OBJECTS:
        return name

    for obj in HOUSEHOLD_OBJECTS:
        if len(obj) > 2 and (obj in name or name in obj):
            return CANONICAL.get(obj, obj)

    return name

def merge_detections(detections_per_frame: List[List[str]]) -> List[Dict]:
    max_counts: Dict[str, int] = {}
    for frame_detections in detections_per_frame:
        frame_counts: Dict[str, int] = {}
        for raw in frame_detections:
            canonical = normalize_object_name(raw)
            if canonical:
                frame_counts[canonical] = frame_counts.get(canonical, 0) + 1

        for k, v in frame_counts.items():
            max_counts[k] = max(max_counts.get(k, 0), v)

    inventory = [
        {"name": k, "quantity": min(v, 10)}
        for k, v in max_counts.items() if k
    ]
    inventory.sort(key=lambda x: x["quantity"], reverse=True)
    return inventory
