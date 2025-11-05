from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Annotated
from contextlib import asynccontextmanager
import io
import tempfile
from pathlib import Path
from yolo_module import load_model, detect_with_annotated_image

# Global model variable
model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the YOLO model when the application starts and cleanup on shutdown"""
    global model
    # Startup
    try:
        model = load_model("model/best.pt")
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        raise

    yield

    # Shutdown (cleanup if needed)
    print("Shutting down...")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Traffic Sign Detection API",
    description="API for detecting traffic signs using YOLOv8",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=False,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files (frontend)
# Support both local dev and Docker paths
frontend_path = Path(__file__).parent / "frontend"
if not frontend_path.exists():
    frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


@app.get("/")
async def root():
    """Serve the frontend application"""
    frontend_index = frontend_path / "index.html"
    if frontend_index.exists():
        return FileResponse(frontend_index)
    return {
        "message": "Traffic Sign Detection API",
        "status": "running",
        "endpoints": {"detect": "/detect", "health": "/health"},
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model_loaded": model is not None}


@app.post("/detect")
async def detect_traffic_signs(
    file: Annotated[
        UploadFile, File(description="Image file for traffic sign detection")
    ],
    conf: float = 0.25,
    iou: float = 0.45,
):
    """
    Detect traffic signs in an uploaded image.

    Args:
        file: Image file (JPEG, PNG, etc.)
        conf: Confidence threshold (0.0-1.0, default: 0.25)
        iou: IoU threshold for NMS (0.0-1.0, default: 0.45)

    Returns:
        JSON with detection results including class, confidence, and bounding boxes
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, detail=f"File must be an image. Got: {file.content_type}"
        )

    # Create a temporary file to save the uploaded image
    temp_file_path = None
    try:
        # Read the uploaded file
        image_bytes = await file.read()

        # Get file extension from filename
        file_extension = Path(file.filename or "image.jpg").suffix or ".jpg"

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension
        ) as temp_file:
            _ = temp_file.write(image_bytes)
            temp_file_path = temp_file.name

        # Perform detection using the temporary file path
        detection_results, _ = detect_with_annotated_image(
            model=model, source=temp_file_path, conf=conf, iou=iou, image_format="JPEG"
        )

        return {
            "filename": file.filename,
            "detections": detection_results,
            "detection_count": len(detection_results),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

    finally:
        # Clean up temporary file
        if temp_file_path is not None:
            try:
                Path(temp_file_path).unlink(missing_ok=True)
            except Exception:
                pass


@app.post("/detect/image")
async def detect_with_image(
    file: Annotated[
        UploadFile, File(description="Image file for traffic sign detection")
    ],
    conf: float = 0.25,
    iou: float = 0.45,
):
    """
    Detect traffic signs and return the annotated image.

    Args:
        file: Image file (JPEG, PNG, etc.)
        conf: Confidence threshold (0.0-1.0, default: 0.25)
        iou: IoU threshold for NMS (0.0-1.0, default: 0.45)

    Returns:
        Annotated image with bounding boxes drawn on detected traffic signs
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400, detail=f"File must be an image. Got: {file.content_type}"
        )

    # Create a temporary file to save the uploaded image
    temp_file_path = None
    try:
        # Read the uploaded file
        image_bytes = await file.read()

        # Get file extension from filename
        file_extension = Path(file.filename or "image.jpg").suffix or ".jpg"

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_extension
        ) as temp_file:
            _ = temp_file.write(image_bytes)
            temp_file_path = temp_file.name

        # Perform detection using the temporary file path
        _, annotated_image_bytes = detect_with_annotated_image(
            model=model, source=temp_file_path, conf=conf, iou=iou, image_format="JPEG"
        )

        # Return the annotated image
        return StreamingResponse(
            io.BytesIO(annotated_image_bytes),
            media_type="image/jpeg",
            headers={
                "Content-Disposition": f'inline; filename="annotated_{file.filename}"'
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

    finally:
        # Clean up temporary file
        if temp_file_path is not None:
            try:
                Path(temp_file_path).unlink(missing_ok=True)
            except Exception:
                pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
