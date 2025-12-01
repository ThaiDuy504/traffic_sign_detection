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


def get_sign_color_scheme(class_key: str) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    """
    Get color scheme for traffic sign based on its type.
    Returns (box_color, text_bg_color, text_color) in RGB format.
    
    Colors are carefully selected to be easy on the eyes and provide good contrast.
    """
    # Prohibitory signs (P.*) - Red theme (softer red)
    if class_key.startswith('P.'):
        return (
            (220, 50, 50),    # Soft red box
            (180, 30, 30),    # Dark red background
            (255, 255, 255)   # White text
        )
    
    # Warning signs (W.*) - Yellow/Orange theme
    elif class_key.startswith('W.'):
        return (
            (255, 165, 0),    # Orange box
            (204, 102, 0),    # Dark orange background
            (255, 255, 255)   # White text
        )
    
    # Regulatory/Mandatory signs (R.*) - Blue theme
    elif class_key.startswith('R.'):
        return (
            (70, 130, 220),   # Soft blue box
            (30, 80, 150),    # Dark blue background
            (255, 255, 255)   # White text
        )
    
    # Information/Guide signs (I.*) - Green theme
    elif class_key.startswith('I.'):
        return (
            (60, 180, 75),    # Soft green box
            (30, 120, 50),    # Dark green background
            (255, 255, 255)   # White text
        )
    
    # Speed limit signs (S.*) - Purple theme
    elif class_key.startswith('S.'):
        return (
            (147, 112, 219),  # Medium purple box
            (85, 60, 140),    # Dark purple background
            (255, 255, 255)   # White text
        )
    
    # Bus signs (B.*) - Teal theme
    elif class_key.startswith('B.'):
        return (
            (64, 224, 208),   # Turquoise box
            (32, 140, 130),   # Dark teal background
            (255, 255, 255)   # White text
        )
    
    # Camera - Pink/Magenta theme
    elif 'Camera' in class_key or 'camera' in class_key:
        return (
            (255, 105, 180),  # Hot pink box
            (200, 60, 130),   # Dark pink background
            (255, 255, 255)   # White text
        )
    
    # Default - Gray theme for unknown types
    else:
        return (
            (128, 128, 128),  # Gray box
            (80, 80, 80),     # Dark gray background
            (255, 255, 255)   # White text
        )


def check_overlap(rect1: tuple[float, float, float, float], 
                  rect2: tuple[float, float, float, float]) -> bool:
    """
    Check if two rectangles overlap.
    rect format: (x1, y1, x2, y2)
    """
    x1_1, y1_1, x2_1, y2_1 = rect1
    x1_2, y1_2, x2_2, y2_2 = rect2
    
    # No overlap if one is to the left/right/above/below the other
    if x2_1 < x1_2 or x2_2 < x1_1:
        return False
    if y2_1 < y1_2 or y2_2 < y1_1:
        return False
    
    return True


def find_non_overlapping_position(
    box_coords: tuple[float, float, float, float],
    text_width: float,
    text_height: float,
    img_width: int,
    img_height: int,
    occupied_regions: list[tuple[float, float, float, float]],
    padding: int = 5
) -> tuple[float, float]:
    """
    Find optimal position for label that doesn't overlap with existing labels.
    Returns (text_x, text_y)
    """
    x1, y1, x2, y2 = box_coords
    text_w = text_width + padding * 2
    text_h = text_height + padding * 2
    
    # List of candidate positions (in priority order)
    candidates = [
        # Above box
        (x1, y1 - text_h - 5),
        # Below box
        (x1, y2 + 5),
        # Right of box
        (x2 + 5, y1),
        # Left of box
        (x1 - text_w - 5, y1),
        # Top-left inside box
        (x1 + 5, y1 + 5),
        # Top-right inside box
        (x2 - text_w - 5, y1 + 5),
        # Bottom-left inside box
        (x1 + 5, y2 - text_h - 5),
        # Bottom-right inside box
        (x2 - text_w - 5, y2 - text_h - 5),
        # Center inside box
        ((x1 + x2 - text_w) / 2, (y1 + y2 - text_h) / 2),
    ]
    
    for text_x, text_y in candidates:
        # Ensure within image bounds
        text_x = max(0, min(text_x, img_width - text_w))
        text_y = max(0, min(text_y, img_height - text_h))
        
        # Create rectangle for this position
        candidate_rect = (text_x, text_y, text_x + text_w, text_y + text_h)
        
        # Check if it overlaps with any existing label
        has_overlap = False
        for occupied in occupied_regions:
            if check_overlap(candidate_rect, occupied):
                has_overlap = True
                break
        
        if not has_overlap:
            return text_x, text_y
    
    # If all positions overlap, return the first candidate (above box) as fallback
    text_x, text_y = candidates[0]
    text_x = max(0, min(text_x, img_width - text_w))
    text_y = max(0, min(text_y, img_height - text_h))
    return text_x, text_y


def draw_annotations(
    image: np.ndarray,
    boxes,
    names: dict,
    class_mapping: dict[str, str] | None = None,
) -> np.ndarray:
    """
    Draw bounding boxes and labels on image with custom styling for better visibility.
    Each sign type gets a unique color scheme for easy identification.
    Labels are positioned to avoid overlapping with each other.

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

    # Get image dimensions
    img_width, img_height = pil_img.size
    
    # Track occupied regions to prevent label overlap
    occupied_regions: list[tuple[float, float, float, float]] = []

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

            # Get color scheme based on sign type
            box_color, text_bg_color, text_color = get_sign_color_scheme(class_key)

            # Draw bounding box with thicker line
            line_width = 3
            draw.rectangle([x1, y1, x2, y2], outline=box_color, width=line_width)

            # Calculate text size
            try:
                bbox = draw.textbbox((0, 0), label, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                # Fallback for older PIL versions
                text_width, text_height = draw.textsize(label, font=font)

            padding = 5
            
            # Find non-overlapping position for this label
            text_x, text_y = find_non_overlapping_position(
                (x1, y1, x2, y2),
                text_width,
                text_height,
                img_width,
                img_height,
                occupied_regions,
                padding
            )
            
            # Add this label's region to occupied list
            text_rect = (
                text_x,
                text_y,
                text_x + text_width + padding * 2,
                text_y + text_height + padding * 2
            )
            occupied_regions.append(text_rect)

            # Draw text background rectangle for better readability
            draw.rectangle(
                [text_rect[0], text_rect[1], text_rect[2], text_rect[3]],
                fill=text_bg_color,
            )

            # Draw text
            draw.text((text_x + padding, text_y + padding), label, fill=text_color, font=font)

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
