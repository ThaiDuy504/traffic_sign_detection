from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Annotated
from contextlib import asynccontextmanager
import io
import tempfile
import os
import cv2
import numpy as np
from pathlib import Path
from yolo_module import load_model, detect_with_annotated_image, load_class_mapping, process_video

# Global model variable
model = None
class_mapping = None

# Inference settings
INFERENCE_IMGSZ = 640  # Smaller = faster, larger = more accurate (default: 640)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the YOLO model when the application starts and cleanup on shutdown"""
    global model, class_mapping
    # Startup
    try:
        model = load_model("model/best.pt")
        print("✓ Model loaded successfully")
        
        # Load class mapping
        class_mapping = load_class_mapping("class_mapping.txt")
        print(f"✓ Class mapping loaded: {len(class_mapping)} classes")
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
    conf: float = 0.5,
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
            model=model, source=temp_file_path, conf=conf, iou=iou, image_format="JPEG", class_mapping=class_mapping
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
    conf: float = 0.5,
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
            model=model, source=temp_file_path, conf=conf, iou=iou, image_format="JPEG", class_mapping=class_mapping
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


@app.post("/detect/video")
async def detect_video(
    file: Annotated[
        UploadFile, File(description="Video file for traffic sign detection")
    ],
    background_tasks: BackgroundTasks,
    conf: float = 0.5,
    iou: float = 0.45,
):
    """
    Detect traffic signs in an uploaded video.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Validate file type
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=400, detail=f"File must be a video. Got: {file.content_type}"
        )

    temp_file_path = None
    processed_path = None
    try:
        # Create temporary file for input video
        file_extension = Path(file.filename or "video.mp4").suffix or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        # Process video
        processed_path = process_video(
            model=model, source_path=temp_file_path, conf=conf, iou=iou
        )

        # Clean up input file immediately
        Path(temp_file_path).unlink(missing_ok=True)
        temp_file_path = None

        # Schedule cleanup of processed file
        background_tasks.add_task(os.unlink, processed_path)

        return FileResponse(
            processed_path, 
            media_type="video/mp4", 
            filename=f"annotated_{file.filename}"
        )

    except Exception as e:
        # Clean up on error
        if temp_file_path and Path(temp_file_path).exists():
            Path(temp_file_path).unlink(missing_ok=True)
        if processed_path and Path(processed_path).exists():
            Path(processed_path).unlink(missing_ok=True)
            
        raise HTTPException(status_code=500, detail=f"Video processing failed: {str(e)}")


# Store active video processing sessions
video_sessions: dict[str, str] = {}  # session_id -> temp_file_path


@app.post("/detect/video/upload")
async def upload_video_for_streaming(
    file: Annotated[UploadFile, File(description="Video file")],
):
    """Upload video and get session ID for streaming processing."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail=f"File must be a video. Got: {file.content_type}")

    # Save video to temp file
    file_extension = Path(file.filename or "video.mp4").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        temp_file.write(await file.read())
        temp_file_path = temp_file.name

    # Generate session ID
    import uuid
    session_id = str(uuid.uuid4())
    video_sessions[session_id] = temp_file_path

    # Get video info
    cap = cv2.VideoCapture(temp_file_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.release()

    return {
        "session_id": session_id,
        "total_frames": total_frames,
        "fps": fps,
        "filename": file.filename,
    }


@app.websocket("/ws/video/{session_id}")
async def websocket_video(websocket: WebSocket, session_id: str):
    """Stream video processing frame by frame via WebSocket."""
    await websocket.accept()

    if model is None:
        await websocket.send_json({"error": "Model not loaded"})
        await websocket.close()
        return

    if session_id not in video_sessions:
        await websocket.send_json({"error": "Invalid session ID"})
        await websocket.close()
        return

    temp_file_path = video_sessions.pop(session_id)

    try:
        query_params = websocket.query_params
        conf = float(query_params.get("conf", 0.25))
        iou = float(query_params.get("iou", 0.45))

        cap = cv2.VideoCapture(temp_file_path)
        if not cap.isOpened():
            await websocket.send_json({"error": "Could not open video"})
            await websocket.close()
            return

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30

        await websocket.send_json({
            "type": "metadata",
            "total_frames": total_frames,
            "fps": fps
        })

        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            results = model.predict(frame, conf=conf, iou=iou, verbose=False)
            annotated = results[0].plot()

            _, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
            await websocket.send_bytes(buffer.tobytes())
            frame_idx += 1

        cap.release()
        await websocket.send_json({"type": "done", "frames_processed": frame_idx})

    except WebSocketDisconnect:
        print("Video WS client disconnected")
    except Exception as e:
        print(f"Video WS error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        if Path(temp_file_path).exists():
            Path(temp_file_path).unlink(missing_ok=True)
        try:
            await websocket.close()
        except:
            pass


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    if model is None:
        await websocket.close(code=1011, reason="Model not loaded")
        return

    try:
        # Extract query parameters manually since FastAPI doesn't inject them for WebSockets
        query_params = websocket.query_params
        conf = float(query_params.get("conf", 0.25))
        iou = float(query_params.get("iou", 0.45))
        
        while True:
            data = await websocket.receive_bytes()
            
            # Convert bytes to numpy array
            nparr = np.frombuffer(data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                continue
                
            # Detect and get annotated image
            # We pass the numpy array directly
            _, annotated_bytes = detect_with_annotated_image(
                model=model, 
                source=img, 
                conf=conf, 
                iou=iou, 
                image_format="JPEG",
                class_mapping=class_mapping,
                imgsz=INFERENCE_IMGSZ,
            )
            
            await websocket.send_bytes(annotated_bytes)
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
