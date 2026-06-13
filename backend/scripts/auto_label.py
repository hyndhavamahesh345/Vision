from ultralytics import YOLO
from pathlib import Path

# Load extra-large zero-shot model
model = YOLO("yolov8x-worldv2.pt")

CLASSES = ["projector", "chimney", "air conditioner", "table", "chair", "water heater", "ceiling fan", "light switch", "bed", "sofa", "television", "refrigerator"]
model.set_classes(CLASSES)

images_dir = Path("dataset/images/train")
labels_dir = Path("dataset/labels/train")
labels_dir.mkdir(parents=True, exist_ok=True)

# Generate dataset.yaml
yaml_path = Path("dataset/dataset.yaml")
yaml_content = f"""path: {Path("dataset").absolute()}
train: images/train
val: images/train

nc: {len(CLASSES)}
names: {CLASSES}
"""
with open(yaml_path, "w") as f:
    f.write(yaml_content)

image_files = list(images_dir.glob("*.jpg"))
print(f"Auto-labeling {len(image_files)} images...")

labeled_count = 0
for img_path in image_files:
    # Use low confidence to capture as much as possible for fine-tuning
    res = model.predict(str(img_path), conf=0.02, verbose=False)[0]
    
    label_path = labels_dir / (img_path.stem + ".txt")
    with open(label_path, "w") as f:
        if res.boxes is not None and len(res.boxes) > 0:
            for box in res.boxes:
                cls_id = int(box.cls[0])
                # Normalized xywh
                x, y, w, h = box.xywhn[0]
                f.write(f"{cls_id} {x} {y} {w} {h}\n")
            labeled_count += 1
            
print(f"Finished auto-labeling! Found objects in {labeled_count} images.")
