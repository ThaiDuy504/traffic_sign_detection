from ultralytics import YOLO  # type: ignore
from pathlib import Path
import numpy as np
from PIL import Image
import io


def load_model(model_path: str = "model/best.pt") -> YOLO:
    """
    Load a YOLOv8 model from the specified path.

    Args:
        model_path: Path to the model weights (default: "model/best.pt")

    Returns:
        Loaded YOLO model instance
    """
    return YOLO(model_path)


def detect_with_annotated_image(
    model: YOLO,
    source: str | Path | np.ndarray,
    conf: float = 0.25,
    iou: float = 0.45,
    image_format: str = "JPEG",
) -> tuple[list[dict[str, int | str | float | dict[str, float]]], bytes]:
    """
    Perform detection and return both results and annotated image for frontend rendering.
    Optimized to work with temporary file paths from main.py.

    Args:
        model: Pre-loaded YOLO model instance
        source: Image source (temporary file path from main.py or numpy array)
        conf: Confidence threshold (default: 0.25)
        iou: NMS IoU threshold (default: 0.45)
        image_format: Output image format for frontend (JPEG, PNG, etc.)

    Returns:
        Tuple of (detection_results, annotated_image_bytes)
        - detection_results: List of dictionaries containing:
            - index: Detection index number
            - class: Detected object class name
            - confidence: Detection confidence/accuracy (0-1)
            - bbox: Bounding box coordinates {x1, y1, x2, y2}
        - annotated_image_bytes: Image bytes with drawn bounding boxes for frontend
    """
    # Run prediction on the source (typically a temporary file path from main.py)
    results = model.predict(  # type: ignore
        source=source, save=False, conf=conf, iou=iou, verbose=False
    )

    # Process first result (single image)
    result = results[0]

    # Get annotated image as numpy array (BGR format with boxes drawn)
    annotated_img = result.plot()

    # Convert BGR to RGB
    img_rgb = annotated_img[:, :, ::-1]

    # Convert to PIL Image and then to bytes
    pil_img = Image.fromarray(img_rgb)
    img_bytes = io.BytesIO()
    pil_img.save(img_bytes, format=image_format)
    _ = img_bytes.seek(0)
    annotated_image_bytes = img_bytes.getvalue()

    # Parse detection results
    detection_results: list[dict[str, int | str | float | dict[str, float]]] = []

    if result.boxes is not None and len(result.boxes) > 0:
        boxes = result.boxes
        for i in range(len(boxes)):
            box = boxes[i]
            cls = int(box.cls[0])
            confidence = float(box.conf[0])
            class_name = result.names[cls]

            # Get bounding box coordinates
            bbox = box.xyxy[0].tolist()  # type: ignore  # [x1, y1, x2, y2]

            detection: dict[str, int | str | float | dict[str, float]] = {
                "index": i + 1,
                "class": class_name,
                "confidence": confidence,  # This is the accuracy/confidence score
                "bbox": {
                    "x1": bbox[0],
                    "y1": bbox[1],
                    "x2": bbox[2],
                    "y2": bbox[3],
                },
            }

            detection_results.append(detection)

    return detection_results, annotated_image_bytes
