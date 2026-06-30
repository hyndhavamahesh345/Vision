import os
from typing import Optional, List, Dict

# ── Household Vocabulary ──────────────────────────────────────────────────────
HOUSEHOLD_OBJECTS = [
    "sofa", "couch", "chair", "armchair", "table", "dining table", "coffee table", "meeting table", "conference table",
    "desk", "tv", "television", "monitor", "bed", "mattress", "wardrobe", "closet",
    "cabinet", "cupboard", "refrigerator", "fridge", "fan", "ceiling fan", "table fan", "pedestal fan", "exhaust fan", "wall fan", "light",
    "lamp", "chandelier", "floor lamp", "table lamp", "wall light", "ceiling light", "bulb", "light bulb",
    "door", "window", "shelf", "bookshelf", "rack",
    "clock", "rug", "carpet",
    "washing machine", "microwave", "oven", "stove", "sink", "toilet", "bathtub", "commode",
    "shower", "mirror", "pillow", "cushion",
    "blanket", "air conditioner", "heater", "water heater", "geyser", "bathroom water heater", "wall-mounted water heater", "water boiler", "water tank", "hot water dispenser", "water cylinder", "fireplace", "staircase",
    "drawer", "nightstand", "bench", "ottoman", "bookcase",
    "dishwasher", "dryer", "power plugs", "light switch",
    "curtain", "blinds", "water purifier", "ro purifier", "gas cylinder", "mixer grinder", "blender", "trash can", "dustbin", "balcony railing", "grill", "washbasin", "tubelight", "swing", "inverter",
    "chimney", "ac", "office chair", "dining chair", "l-shaped sofa", "gaming chair", "bar stool", "bunk bed", "furniture",
    "diwan cot", "divan cot", "unknown object", "plant", "potted plant", "bottle", "mop", "broom", "bucket", "gate", "tv unit", "dressing table"
, "shoe rack", "shoe cabinet", "coat rack", "doormat", "ironing board", "iron", "vacuum cleaner", "laundry basket", "clothes drying rack", "wall clock", "plant pot", "vase", "picture frame", "painting", "wall art", "sculpture", "statue", "candle", "tissue box", "waste bin", "dustpan", "mop bucket", "soap dispenser", "towel rack", "towel", "bath mat", "shower curtain", "toilet paper holder", "toilet brush", "hair dryer", "humidifier", "dehumidifier", "purifier", "radiator", "thermostat", "smoke detector", "fire extinguisher", "ladder", "router", "modem", "smart speaker", "security camera", "safe", "storage box", "basket", "bookend", "whiteboard", "ironing stand", "study chair", "bean bag", "console table", "bidet", "shower head", "exhaust hood", "rice cooker", "toaster", "air fryer", "coffee maker", "water cooler", "kettle", "wine cooler", "center table", "tv stand", "plate", "bowl", "cup", "glass", "mug", "wine glass", "fork", "spoon", "knife", "spatula", "pot", "pan", "frying pan", "saucepan", "cutting board", "baking sheet", "measuring cup", "kitchen scale", "pepper shaker", "salt shaker", "spice rack", "dish rack", "can opener", "bottle opener", "corkscrew", "pizza cutter", "peeler", "grater", "colander", "strainer", "food processor", "juicer", "hand mixer", "stand mixer", "waffle maker", "sandwich maker", "electric grill", "slow cooker", "pressure cooker", "microwave oven", "kitchen island", "kitchen cabinet", "projector", "projector screen", "soundbar", "home theater system", "subwoofer", "record player", "turntable", "vinyl record", "cd player", "dvd player", "blu-ray player", "gaming console", "playstation", "xbox", "nintendo switch", "video game controller", "remote control", "tv remote", "set-top box", "cable box", "streaming device", "bookshelf speaker", "floorstanding speaker", "magazine rack", "fireplace mantel", "bean bag chair", "floor cushion", "throw pillow", "throw blanket", "area rug", "trundle bed", "daybed", "futon", "air mattress", "headboard", "footboard", "bed frame", "bedsheet", "duvet", "comforter", "quilt", "sleeping bag", "clothes hanger", "coat hanger", "shoe horn", "shoe tree", "laundry hamper", "ironing board cover", "wardrobe cabinet", "dresser", "makeup mirror", "vanity table", "toothbrush", "toothpaste", "mouthwash", "dental floss", "hairbrush", "comb", "hair straightener", "curling iron", "shaving razor", "electric shaver", "shaving cream", "shampoo bottle", "conditioner bottle", "body wash bottle", "lotion bottle", "soap bar", "liquid soap dispenser", "loofah", "bath sponge", "bath towel", "hand towel", "washcloth", "toilet paper", "toilet plunger", "toilet seat", "bathroom scale", "medicine cabinet", "laptop", "desktop computer", "computer monitor", "computer keyboard", "computer mouse", "mouse pad", "printer", "scanner", "photocopier", "shredder", "office desk", "filing cabinet", "paperweight", "desk lamp", "desk organizer", "pen", "pencil", "marker", "highlighter", "stapler", "scissors", "tape dispenser", "calculator", "notebook", "notepad", "binder", "folder", "clipboard", "whiteboard marker", "eraser", "hammer", "screwdriver", "wrench", "pliers", "tape measure", "power drill", "toolbox", "stepladder", "extension cord", "power strip", "surge protector", "flashlight", "lantern", "umbrella", "raincoat", "boots", "sneakers", "sandals", "slippers", "backpack", "suitcase", "duffel bag", "gym bag", "briefcase", "purse", "wallet", "keys", "keychain", "wall mirror", "full-length mirror", "floor mirror", "table clock", "grandfather clock", "alarm clock", "figurine", "snow globe", "music box", "incense burner", "essential oil diffuser", "air purifier", "water filter", "water pitcher", "indoor plant", "artificial plant", "flower vase", "photo frame", "poster", "tapestry", "window blinds", "window shades", "curtain rod"
]

FAST_MODE = os.getenv("FAST_MODE", "false").lower() == "true"

CORE_HOUSEHOLD_OBJECTS = [
    "sofa", "l-shaped sofa", "chair", "armchair", "office chair", "dining chair", "gaming chair", "bar stool", 
    "table", "dining table", "coffee table", "desk", 
    "tv", "bed", "bunk bed", "diwan cot", "divan cot", "wardrobe", "closet", "cabinet", "cupboard", 
    "refrigerator", "fan", "ceiling fan", "table fan", "pedestal fan", "exhaust fan", "wall fan",
    "light", "lamp", "chandelier", "floor lamp", "table lamp", "wall light", "ceiling light", "bulb", "light bulb",
    "door", "window", "shelf", "bookshelf", "clock", "rug", "carpet",
    "washing machine", "microwave", "oven", "stove", 
    "sink", "toilet", "commode", "bathtub", "shower", "mirror", 
    "pillow", "cushion", "blanket", "air conditioner", 
    "heater", "water heater", "geyser", "bathroom water heater", "wall-mounted water heater", "water boiler", "water tank", "hot water dispenser", "water cylinder", "fireplace", "staircase", "drawer", "nightstand", 
    "bench", "ottoman", "dishwasher", "dryer", 
    "power plugs", "light switch", "chimney", "stool", "furniture", "unknown object",
    "curtain", "blinds", "water purifier", "gas cylinder", "mixer grinder", "trash can", "balcony railing", "swing", "inverter",
    "plant", "bottle", "mop", "broom", "bucket", "gate", "tv unit", "dressing table", "wall mirror"
]

if FAST_MODE:
    # Use core subset of objects for 4.5x faster prediction in FAST_MODE
    UNIQUE_HOUSEHOLD_OBJECTS = sorted(list(set(CORE_HOUSEHOLD_OBJECTS)))
else:
    # Keep full list in standard/detailed mode
    UNIQUE_HOUSEHOLD_OBJECTS = sorted(list(set(HOUSEHOLD_OBJECTS)))

CANONICAL = {
    "couch": "sofa", "settee": "sofa",
    "recliner": "armchair", 
    "side table": "table", "end table": "table",
    "television": "tv", "monitor": "tv", "screen": "tv",
    "mattress": "bed",
    "closet": "cabinet", "cupboard": "cabinet", "wardrobe": "cabinet", "cabinet": "cabinet",
    "drawer": "drawer", "chest of drawers": "drawer",
    "fridge": "refrigerator", "freezer": "refrigerator",
    "bookshelf": "shelf", "bookcase": "shelf", "rack": "shelf",
    "washing machine": "washing machine", "microwave": "microwave",
    "oven": "oven", "stove": "stove", "dishwasher": "dishwasher", "dryer": "dryer",
    "ottoman": "bench", "bench": "bench",
    "potted plant": "plant",
    "commode": "toilet",

    "pillow": "pillow",
    "air conditioner": "air conditioner", "heater": "heater", "water heater": "geyser", "geyser": "geyser", "ac": "air conditioner", "bathroom water heater": "geyser", "wall-mounted water heater": "geyser", "water boiler": "geyser", "small water tank": "geyser", "water tank": "geyser", "hot water dispenser": "geyser", "water cylinder": "geyser",
    "power plugs and sockets": "power plugs", "power outlet": "power plugs",
    "power plug": "power plugs", "socket": "power plugs", "electrical outlet": "power plugs",
    "outlet": "power plugs", "plug": "power plugs",
    "light switch": "light switch", "switch": "light switch",
    "door handle": "door", "door knob": "door", "door frame": "door", "doorframe": "door",
    "window frame": "window",
    "sink faucet": "sink", "faucet": "sink", "tap": "sink", "kitchen sink": "sink", "bathroom sink": "sink", "washbasin": "sink",
    "chimney": "chimney",
    "ro purifier": "water purifier", "aquaguard": "water purifier",
    "blender": "mixer grinder", "mixer": "mixer grinder",
    "dustbin": "trash can", "garbage can": "trash can",
    "grill": "balcony railing", "railing": "balcony railing",
    "tubelight": "light", "led light": "light",
    "jhula": "swing",
    "battery": "inverter",
    "light bulb": "bulb"
}

def normalize_object_name(raw_name: str) -> Optional[str]:
    if raw_name is None:
        return None
    name = str(raw_name).lower().strip()
    
    if name in ["person", "curtain", "blinds", "tree", "flower", "bird", "animal", "dog", "cat", "man", "woman", "boy", "girl"]:
        return None

    if name in CANONICAL:
        return CANONICAL[name]

    if name in HOUSEHOLD_OBJECTS:
        return name

    for obj in HOUSEHOLD_OBJECTS:
        if len(obj) > 2 and (obj in name or name in obj):
            return CANONICAL.get(obj, obj)

    # STRICT FILTERING: If the AI detects something completely unknown like 'bird', delete it immediately.
    return None

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

