"""
Run a trained YOLOv8 model on one CCTV image to get:
  1. Vehicle detection + classification (bounding boxes per class)
  2. Per-class vehicle counts
  3. A congestion level (LIGHT / MODERATE / HEAVY) from the total vehicle count
"""

from functools import lru_cache
from pathlib import Path

from django.core.files.base import ContentFile
from django.utils import timezone

CONGESTION_THRESHOLDS = {
    "LIGHT": (0, 8),
    "MODERATE": (8, 20),
    "HEAVY": (20, float("inf")),
}


def classify_congestion(vehicle_count: int) -> str:
    for level, (low, high) in CONGESTION_THRESHOLDS.items():
        if low <= vehicle_count < high:
            return level
    return "HEAVY"


@lru_cache(maxsize=2)
def get_model(weights_path: str):
    """Load the YOLO model once and reuse it, so bulk uploads don't reload it for every image."""
    from ultralytics import YOLO

    return YOLO(weights_path)


def run_inference(cctv_image, weights_path: str):
    import cv2
    from traffic.models import VehicleClassCount

    model = get_model(weights_path)
    results = model.predict(
        source=cctv_image.image.path, conf=0.4, save=False, verbose=False
    )[0]

    class_counts = {}
    confidences = {}
    for box in results.boxes:
        cls_name = results.names[int(box.cls[0])]
        conf = float(box.conf[0])
        class_counts[cls_name] = class_counts.get(cls_name, 0) + 1
        confidences.setdefault(cls_name, []).append(conf)

    total = sum(class_counts.values())

    annotated_array = results.plot(line_width=2, font_size=10, labels=True, conf=True)
    ok, buffer = cv2.imencode(".jpg", annotated_array)
    if ok:
        filename = f"annotated_{Path(cctv_image.image.name).stem}.jpg"
        cctv_image.annotated_image.save(filename, ContentFile(buffer.tobytes()), save=False)

    cctv_image.total_vehicle_count = total
    cctv_image.congestion_level = classify_congestion(total)
    cctv_image.processed_at = timezone.now()
    cctv_image.save()

    VehicleClassCount.objects.filter(cctv_image=cctv_image).delete()
    VehicleClassCount.objects.bulk_create([
        VehicleClassCount(
            cctv_image=cctv_image,
            class_name=name,
            count=count,
            avg_confidence=sum(confidences[name]) / len(confidences[name]),
        )
        for name, count in class_counts.items()
    ])

    return cctv_image