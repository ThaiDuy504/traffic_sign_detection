import io
import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO  # type: ignore


def load_class_mapping(mapping_path: str = "class_mapping.txt") -> dict[str, str]:
    """
    Load class mapping from a text file.

    Args:
        mapping_path: Path to the class mapping file (default: "class_mapping.txt")

    Returns:
        Dictionary mapping class keys to Vietnamese descriptions
        Example: {"W.224": "Đường người đi bộ cắt ngang", ...}
    """
    class_mapping: dict[str, str] = {}

    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "=" not in line:
                    continue

                # Split by '=' and clean up whitespace
                parts = line.split("=", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    class_mapping[key] = value
    except FileNotFoundError:
        print(
            f"Warning: Class mapping file '{mapping_path}' not found. Using class keys only."
        )
    except Exception as e:
        print(f"Warning: Error loading class mapping: {e}. Using class keys only.")

    return class_mapping


def load_model(model_path: str = "model/best.pt") -> YOLO:
    """
    Load a YOLOv8 model from the specified path.

    Args:
        model_path: Path to the model weights (default: "model/best.pt")

    Returns:
        Loaded YOLO model instance
    """
    return YOLO(model_path)


def draw_annotations(
    image: np.ndarray,
    boxes,
    names: dict,
    class_mapping: dict[str, str] | None = None,
) -> np.ndarray:
    """
    Draw bounding boxes and labels on image with custom styling for better visibility.

    Args:
        image: Input image as numpy array (BGR format)
        boxes: YOLO detection boxes
        names: Class names dictionary from YOLO model
        class_mapping: Optional mapping from class keys to Vietnamese names

    Returns:
        Annotated image as numpy array (RGB format)
    """
    # Convert BGR to RGB for PIL
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)

    # Try to load a font that supports Vietnamese characters
    try:
        # Try to use Arial Unicode MS or similar font with Vietnamese support
        font_size = 20
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
        except:
            # Fallback to default font if custom font not available
            font = ImageFont.load_default()

    if boxes is not None and len(boxes) > 0:
        for box in boxes:
            # Get box coordinates
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            class_key = names[cls]

            # Get display name (Vietnamese if available)
            if class_mapping and class_key in class_mapping:
                display_name = class_mapping[class_key]
            else:
                display_name = class_key

            # Create label with confidence
            label = f"{display_name} {conf:.2f}"

            # Define colors for better visibility
            # Using bright colors on dark background
            box_color = (0, 255, 0)  # Bright green for box
            text_bg_color = (0, 128, 0)  # Dark green background for text
            text_color = (255, 255, 255)  # White text

            # Draw bounding box with thicker line
            line_width = 3
            draw.rectangle([x1, y1, x2, y2], outline=box_color, width=line_width)

            # Calculate text size and position
            try:
                bbox = draw.textbbox((0, 0), label, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                # Fallback for older PIL versions
                text_width, text_height = draw.textsize(label, font=font)

            # Position text above the box, or below if too close to top
            text_y = y1 - text_height - 5 if y1 > text_height + 10 else y2 + 5

            # Draw text background rectangle for better readability
            padding = 5
            draw.rectangle(
                [
                    x1,
                    text_y - padding,
                    x1 + text_width + padding * 2,
                    text_y + text_height + padding,
                ],
                fill=text_bg_color,
            )

            # Draw text
            draw.text((x1 + padding, text_y), label, fill=text_color, font=font)

    return np.array(pil_img)


def detect_with_annotated_image(
    model: YOLO,
    source: str | Path | np.ndarray,
    conf: float = 0.5,
    iou: float = 0.45,
    image_format: str = "JPEG",
    class_mapping: dict[str, str] | None = None,
    imgsz: int = 1280,
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
        class_mapping: Optional dictionary mapping class keys to Vietnamese descriptions
        imgsz: Inference image size (default: 1280, lower = faster)

    Returns:
        Tuple of (detection_results, annotated_image_bytes)
        - detection_results: List of dictionaries containing:
            - index: Detection index number
            - class: Detected object class key
            - class_name: Vietnamese description (if mapping provided)
            - confidence: Detection confidence/accuracy (0-1)
            - bbox: Bounding box coordinates {x1, y1, x2, y2}
        - annotated_image_bytes: Image bytes with drawn bounding boxes for frontend
    """
    # Run prediction on the source (typically a temporary file path from main.py)
    results = model.predict(  # type: ignore
        source=source, save=False, conf=conf, iou=iou, verbose=False, imgsz=imgsz
    )

    # Process first result (single image)
    result = results[0]

    # Get original image
    original_img = result.orig_img  # BGR format

    # Draw custom annotations with Vietnamese names
    annotated_img_rgb = draw_annotations(
        original_img, result.boxes, result.names, class_mapping
    )

    # Convert to PIL Image and then to bytes
    pil_img = Image.fromarray(annotated_img_rgb)
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
            class_key = result.names[cls]

            # Get bounding box coordinates
            bbox = box.xyxy[0].tolist()  # type: ignore  # [x1, y1, x2, y2]

            detection: dict[str, int | str | float | dict[str, float]] = {
                "index": i + 1,
                "class": class_key,
                "confidence": confidence,  # This is the accuracy/confidence score
                "bbox": {
                    "x1": bbox[0],
                    "y1": bbox[1],
                    "x2": bbox[2],
                    "y2": bbox[3],
                },
            }

            # Add Vietnamese class name if mapping is provided
            if class_mapping and class_key in class_mapping:
                detection["class_name"] = class_mapping[class_key]

            detection_results.append(detection)

    return detection_results, annotated_image_bytes


def process_video(
    model: YOLO,
    source_path: str,
    conf: float = 0.5,
    iou: float = 0.45,
    class_mapping: dict[str, str] | None = None,
) -> str:
    """
    Process a video file frame by frame, detecting objects and saving the annotated video.

    Args:
        model: Pre-loaded YOLO model instance
        source_path: Path to the input video file
        conf: Confidence threshold
        iou: NMS IoU threshold
        class_mapping: Optional dictionary mapping class keys to Vietnamese descriptions

    Returns:
        Path to the processed video file
    """
    cap = cv2.VideoCapture(source_path)
    if not cap.isOpened():
        raise ValueError("Could not open video file")

    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    if fps <= 0:
        fps = 30  # Fallback FPS

    # Create output temporary file
    output_fd, output_path = tempfile.mkstemp(suffix=".mp4")
    os.close(output_fd)

    # Initialize video writer
    # 'mp4v' is widely supported
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # type: ignore
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    if not out.isOpened():
        cap.release()
        raise ValueError("Could not open video writer")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Run detection on the frame
        results = model.predict(frame, conf=conf, iou=iou, verbose=False, imgsz=1280)
        result = results[0]

        # Draw custom annotations with Vietnamese names
        annotated_frame_rgb = draw_annotations(
            frame, result.boxes, result.names, class_mapping
        )

        # Convert RGB back to BGR for video writer
        annotated_frame = cv2.cvtColor(annotated_frame_rgb, cv2.COLOR_RGB2BGR)

        # Write frame
        out.write(annotated_frame)

    cap.release()
    out.release()

    return output_path
