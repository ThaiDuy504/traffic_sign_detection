# GitHub Copilot Instructions for Traffic Sign Detection

## Project Overview

This is a Traffic Sign Detection system using YOLOv8 deep learning model with a FastAPI backend and static web frontend. The system can detect traffic signs in images with high accuracy and return results as JSON or annotated images. The application supports both local development and Docker deployment.

## Tech Stack

### Backend
- **Python**: >= 3.12 (application is compatible with 3.12+)
  - Local: Uses version specified in `backend/.python-version` (3.12)
  - Docker: Uses `python:3.13-slim` base image (newer version, still compatible)
  - Note: Both 3.12 and 3.13 work; the difference is just the base image choice
- **FastAPI**: Modern web framework for building APIs (>= 0.120.4)
  - Includes Uvicorn ASGI server via `fastapi[standard]`
  - Built-in CORS middleware for cross-origin requests
  - Static file serving for frontend assets
- **Ultralytics YOLOv8**: Object detection model (>= 8.3.223)
- **PIL (Pillow)**: Image processing (included with Ultralytics)
- **NumPy**: Array operations (included with Ultralytics)

### Frontend
- **Pure HTML/CSS/JavaScript**: No build tools required
- **Static files**: Served directly by FastAPI via `/static` mount
- **Responsive Design**: Modern UI with drag-and-drop support

### Package Management
- **uv**: Fast Python package manager (preferred)
  - All dependencies managed via `pyproject.toml`
  - Lock file: `uv.lock` for reproducible builds

### Model
- **YOLOv8**: Deep learning model for real-time object detection
- **Model weights**: Stored in `backend/model/best.pt`
- **Training**: Jupyter notebook available in `notebook/train_yolo.ipynb`

### Deployment
- **Docker**: Multi-stage Dockerfile for optimized production builds
- **Container Registry**: Built with uv for fast dependency installation
- **System Dependencies**: OpenCV libraries included in runtime image

## Project Structure

```
traffic_sign_detection/
├── .github/
│   └── copilot-instructions.md  # This file
├── backend/                      # FastAPI backend server
│   ├── model/                    # Model weights directory
│   │   └── best.pt              # Trained YOLO model (required)
│   ├── main.py                   # FastAPI application with endpoints
│   ├── yolo_module.py            # YOLO detection logic
│   ├── pyproject.toml            # Backend dependencies
│   ├── uv.lock                   # Dependency lock file
│   └── .python-version           # Python version (3.12)
├── frontend/                     # Static web frontend
│   ├── index.html               # Main HTML page
│   ├── script.js                # Frontend JavaScript logic
│   ├── style.css                # Styling
│   └── README.md                # Frontend documentation
├── notebook/                     # Training notebooks
│   └── train_yolo.ipynb         # YOLO training notebook
├── dockerfile                    # Docker multi-stage build
├── .dockerignore                 # Docker ignore patterns
└── README.md                     # Project documentation (Vietnamese)
```

## Coding Conventions

### Python Style
- **Follow PEP 8**: Standard Python style guidelines
- **Type Hints**: Always use type hints for function parameters and return values
  - Example: `def detect(model: YOLO, conf: float = 0.25) -> tuple[list[dict], bytes]:`
- **Descriptive Names**: Use clear, descriptive variable and function names
  - Good: `detection_results`, `annotated_image_bytes`
  - Avoid: `res`, `img`, `data`
- **Single Responsibility**: Keep functions focused on one task
- **Async/Await**: Use for all I/O operations in FastAPI endpoints
  - File uploads, file reading, database operations

### Error Handling
- **HTTPException**: Use FastAPI's `HTTPException` for all API errors
  - 400: Bad Request (invalid file type, invalid parameters)
  - 503: Service Unavailable (model not loaded)
  - 500: Internal Server Error (detection failures)
- **Cleanup**: Always clean up temporary files in `finally` blocks
  ```python
  finally:
      if temp_file_path:
          Path(temp_file_path).unlink(missing_ok=True)
  ```
- **Validation**: Validate all input parameters
  - Confidence threshold: 0.0-1.0
  - IoU threshold: 0.0-1.0
  - File types: Check `content_type` starts with "image/"

### API Patterns
- **File Uploads**: Use FastAPI's `Annotated[UploadFile, File()]` pattern
- **Consistent Responses**: Always return structured JSON
  - Include filename, detections array, detection_count
- **HTTP Status Codes**: Use appropriate codes
  - 200: Success
  - 400: Client error
  - 500: Server error
  - 503: Service unavailable
- **Image Responses**: Use `StreamingResponse` with proper headers
  ```python
  StreamingResponse(
      io.BytesIO(image_bytes),
      media_type="image/jpeg",
      headers={"Content-Disposition": f'inline; filename="result.jpg"'}
  )
  ```
- **Health Checks**: Always implement `/health` endpoint

### Frontend Patterns
- **API Communication**: Use Fetch API for backend communication
- **Error Handling**: Display user-friendly error messages
- **Loading States**: Show loading indicators during processing
- **Drag and Drop**: Implement for better UX
- **Responsive Design**: Support mobile and desktop
- **No Build Tools**: Keep frontend simple with vanilla JS

## Development Guidelines

### Setting Up Development Environment

1. **Install uv** (if not already installed):
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Install Dependencies**:
   ```bash
   cd backend
   uv sync  # Installs all dependencies in .venv
   ```

3. **Ensure Model Exists**:
   - Place trained model at `backend/model/best.pt`
   - Server will fail to start if model is missing

### Adding New Features

#### Backend Changes
1. **Model Logic**: Update `yolo_module.py` for detection algorithms
   - Keep functions pure and testable
   - Return structured data types
   
2. **API Endpoints**: Add to `main.py` following patterns
   - Use lifespan context manager for startup/shutdown
   - Validate inputs before processing
   - Clean up resources in finally blocks

3. **Dependencies**: 
   ```bash
   cd backend
   # Edit pyproject.toml to add dependency
   uv add <package-name>  # Automatically updates pyproject.toml and uv.lock
   uv sync                # Install new dependencies
   ```

#### Frontend Changes
1. **HTML**: Modify `frontend/index.html` for structure
2. **Styling**: Update `frontend/style.css` for appearance
3. **Logic**: Edit `frontend/script.js` for functionality
   - Keep API_BASE_URL configurable
   - Handle errors gracefully
   - Provide visual feedback

### Testing Endpoints

#### Interactive Documentation
- Start server and visit: `http://localhost:8000/docs`
- Use Swagger UI to test all endpoints
- View request/response schemas

#### Command Line Testing
```bash
# Health check
curl http://localhost:8000/health

# Detect with JSON response
curl -X POST "http://localhost:8000/detect?conf=0.5&iou=0.45" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/image.jpg"

# Detect with image response
curl -X POST "http://localhost:8000/detect/image?conf=0.5" \
  -F "file=@path/to/image.jpg" \
  --output result.jpg
```

### Performance Considerations

#### Memory Management
- **Temporary Files**: Use for image processing to avoid memory issues
  ```python
  with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
      f.write(image_bytes)
      temp_path = f.name
  ```
- **Cleanup**: Always cleanup temp files in `finally` blocks
- **Model Loading**: Load model once at startup using lifespan event
  - Avoid reloading model per request (expensive)

#### Inference Optimization
- **Confidence Threshold**: Higher values (0.5-0.9) = fewer false positives
  - Lower values (0.1-0.3) = more detections but more false positives
- **IoU Threshold**: Controls Non-Maximum Suppression (NMS)
  - Higher values (0.5-0.7) = keep overlapping boxes
  - Lower values (0.3-0.5) = remove overlapping boxes
- **Batch Processing**: YOLOv8 supports batch inference if needed

### File Handling

#### Supported Formats
- **Input**: JPEG, PNG, BMP, WebP (any format PIL/OpenCV supports)
- **Output**: JPEG (for annotated images), JSON (for detection data)

#### Best Practices
```python
# Always validate content type
if not file.content_type or not file.content_type.startswith("image/"):
    raise HTTPException(400, detail=f"Invalid file type: {file.content_type}")

# Use tempfile for safety
with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
    temp.write(await file.read())
    temp_path = temp.name

# Always cleanup
try:
    # Process file
    results = process(temp_path)
finally:
    Path(temp_path).unlink(missing_ok=True)
```

## API Design Patterns

### Endpoint Structure Template
```python
@app.post("/endpoint")
async def endpoint_name(
    file: Annotated[UploadFile, File(description="Image file for processing")],
    param: float = 0.25,
) -> dict:
    """
    Clear docstring explaining endpoint purpose.
    
    Args:
        file: Image file (JPEG, PNG, etc.)
        param: Parameter description with valid range
    
    Returns:
        Structured response with detection results
        
    Raises:
        HTTPException: 400 for invalid input, 503 if model unavailable
    """
    # 1. Validate model loaded
    if model is None:
        raise HTTPException(503, detail="Model not loaded")
    
    # 2. Validate inputs
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, detail=f"Invalid file type")
    
    # 3. Process with try/except/finally
    temp_path = None
    try:
        # Create temp file and process
        image_bytes = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as f:
            f.write(image_bytes)
            temp_path = f.name
        
        results = process(temp_path)
        return {"status": "success", "results": results}
    
    except Exception as e:
        raise HTTPException(500, detail=f"Processing failed: {str(e)}")
    
    finally:
        # 4. Cleanup resources
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
```

### Response Formats

#### JSON Response Structure
```json
{
    "filename": "image.jpg",
    "detections": [
        {
            "index": 1,
            "class": "stop_sign",
            "confidence": 0.95,
            "bbox": {
                "x1": 120.5,
                "y1": 80.3,
                "x2": 280.7,
                "y2": 240.9
            }
        }
    ],
    "detection_count": 1
}
```

#### Detection Object Fields
- **index**: Sequential number (1-based)
- **class**: String name of detected class (from model)
- **confidence**: Float between 0.0-1.0 (detection certainty)
- **bbox**: Bounding box coordinates
  - **x1, y1**: Top-left corner
  - **x2, y2**: Bottom-right corner

#### Image Response Pattern
```python
return StreamingResponse(
    io.BytesIO(annotated_image_bytes),
    media_type="image/jpeg",
    headers={
        "Content-Disposition": f'inline; filename="annotated_{filename}"'
    }
)
```

### Lifespan Management
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load resources on startup, cleanup on shutdown"""
    global model
    # Startup: Load model
    try:
        model = load_model("model/best.pt")
        print("✓ Model loaded successfully")
    except Exception as e:
        print(f"✗ Error loading model: {e}")
        raise  # Fail fast if model can't load
    
    yield  # Application runs
    
    # Shutdown: Cleanup (if needed)
    print("Shutting down...")
    # Release resources, close connections, etc.
```

## Common Tasks

### Running the Backend

#### Local Development
```bash
cd backend

# Method 1: Using uvicorn directly (recommended)
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Method 2: Using the main.py __main__ block
uv run python main.py

# Method 3: Without uv (if dependencies already installed)
python main.py
```

#### Docker Deployment
```bash
# Build the image
docker build -t traffic-sign-detection .

# Run the container
docker run -p 8000:8000 traffic-sign-detection

# Access at http://localhost:8000
```

#### Environment Variables (Optional)
```bash
# Set custom port
export PORT=8080
python main.py

# Set model path
export MODEL_PATH=/path/to/model.pt
```

### Adding Dependencies

```bash
cd backend

# Add a single package
uv add package-name

# Add with version constraint
uv add "package-name>=1.0.0"

# Add dev dependency (for testing/linting)
uv add --dev pytest

# Sync all dependencies (after manual pyproject.toml edits)
uv sync

# Update dependencies
uv sync --upgrade
```

### Model Management

#### Updating the Model
1. Train new model using `notebook/train_yolo.ipynb`
2. Copy `best.pt` from training output to `backend/model/`
   ```bash
   cp runs/detect/train/weights/best.pt backend/model/
   ```
3. Restart server to load new model
   - Model loads once during startup via lifespan event
   - No hot-reload for model changes

#### Model Training
```bash
# Open Jupyter notebook
cd notebook
jupyter notebook train_yolo.ipynb

# Follow notebook instructions to:
# 1. Prepare dataset (images + YOLO labels)
# 2. Configure training parameters
# 3. Train model
# 4. Evaluate results
# 5. Export best.pt
```

### Frontend Development

#### File Structure
```
frontend/
├── index.html   # Main HTML structure
├── script.js    # JavaScript logic (API calls, UI interactions)
└── style.css    # Styling (responsive design)
```

#### Making Changes
1. Edit files directly (no build step required)
2. Refresh browser to see changes (Ctrl+F5 for hard refresh)
3. FastAPI serves files via `/static` mount point
4. API base URL in `script.js`: `const API_BASE_URL = 'http://localhost:8000'`

#### Testing Frontend
```bash
# Start backend server first
cd backend
python main.py

# Open browser
http://localhost:8000

# Or use specific static files
http://localhost:8000/static/index.html
http://localhost:8000/static/style.css
http://localhost:8000/static/script.js
```

### Debugging

#### Backend Debugging
```bash
# Enable verbose logging
uv run uvicorn main:app --log-level debug

# Check model predictions
# In yolo_module.py, set verbose=True in model.predict()
results = model.predict(source=source, verbose=True)

# Print detection details
print(f"Detections: {len(result.boxes)}")
print(f"Classes: {result.names}")
print(f"Boxes: {result.boxes.xyxy}")
```

#### Frontend Debugging
```javascript
// Open browser DevTools (F12)
// Check Console for errors
// Network tab to inspect API calls

// Add debug logging in script.js
console.log('File selected:', selectedFile);
console.log('API response:', data);
```

#### Common Issues
1. **Model not found**: Ensure `backend/model/best.pt` exists
2. **CORS errors**: Check CORS middleware configuration in main.py
3. **Port already in use**: Change port in uvicorn command
4. **Out of memory**: Reduce image size or batch size

## Docker Deployment

### Dockerfile Overview
The project uses a **multi-stage build** for optimized container size:

1. **Build Stage**: Installs dependencies using uv
   - Base: `python:3.13-slim`
   - Uses uv for fast dependency installation
   - Caches dependencies in Docker layers
   
2. **Runtime Stage**: Minimal production image
   - Installs OpenCV system dependencies (libgl1, libglib2.0-0, etc.)
   - Copies only necessary files from build stage
   - Runs as non-root user (appuser) for security
   - Working directory: `/app/backend`

### Building the Image

```bash
# Build with default tag
docker build -t traffic-sign-detection .

# Build with custom tag
docker build -t myregistry/traffic-sign:v1.0.0 .

# Build with build args (if needed)
docker build --build-arg PYTHON_VERSION=3.13 -t traffic-sign-detection .
```

### Running the Container

```bash
# Basic run
docker run -p 8000:8000 traffic-sign-detection

# Run with custom port mapping
docker run -p 8080:8000 traffic-sign-detection

# Run in detached mode
docker run -d -p 8000:8000 --name traffic-detector traffic-sign-detection

# Run with volume mount (for custom model)
docker run -p 8000:8000 \
  -v /path/to/model.pt:/app/backend/model/best.pt \
  traffic-sign-detection

# View logs
docker logs -f traffic-detector
```

### Docker Compose (Optional)

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./backend/model/best.pt:/app/backend/model/best.pt
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

### Important Notes

- **Model Required**: The model file (`backend/model/best.pt`) must exist before building
- **File Paths**: Frontend files are copied to `/app/frontend` in container
- **Static Files**: FastAPI checks frontend paths in order (from main.py):
  - First: `Path(__file__).parent / "frontend"` → `/app/backend/frontend` (doesn't exist in Docker)
  - Fallback: `Path(__file__).parent.parent / "frontend"` → `/app/frontend` (used in Docker)
  - The fallback path matches the Docker copy location, so frontend loads correctly
- **Security**: Container runs as non-root user (UID 1001)
- **Port**: Application listens on port 8000 inside container

## Security Best Practices

### Input Validation

```python
# Always validate file types
if not file.content_type or not file.content_type.startswith("image/"):
    raise HTTPException(400, detail="Invalid file type")

# Validate parameter ranges
if not 0.0 <= conf <= 1.0:
    raise HTTPException(400, detail="Confidence must be between 0.0 and 1.0")

if not 0.0 <= iou <= 1.0:
    raise HTTPException(400, detail="IoU must be between 0.0 and 1.0")
```

### File Handling Security

```python
# Use temporary files, never save uploads permanently
with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
    temp.write(image_bytes)
    temp_path = temp.name

# Always cleanup in finally block
finally:
    if temp_path:
        Path(temp_path).unlink(missing_ok=True)

# Use safe file extensions
allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
ext = Path(file.filename).suffix.lower()
if ext not in allowed_extensions:
    raise HTTPException(400, detail=f"Extension {ext} not allowed")
```

### Resource Limits

```python
# Limit file size using Content-Length header (efficient)
from fastapi import Request

@app.post("/upload")
async def upload_file(request: Request, file: UploadFile):
    # Check Content-Length header before reading
    content_length = request.headers.get('content-length')
    if content_length:
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        if int(content_length) > MAX_FILE_SIZE:
            raise HTTPException(400, detail="File too large")
    
    # Proceed with file processing
    image_bytes = await file.read()
```

### CORS Configuration

```python
# Current: Allows all origins (development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Production: Restrict origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Environment Variables for Secrets

```python
# Never hardcode sensitive data
import os

API_KEY = os.getenv("API_KEY")  # Load from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Use .env file for local development (add to .gitignore)
from dotenv import load_dotenv
load_dotenv()
```

### Docker Security

```dockerfile
# Run as non-root user
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -d /app -s /bin/false appuser
USER appuser

# Don't copy sensitive files (.dockerignore)
.env
.git/
*.key
*.pem
```

## Documentation Standards

### Code Documentation

#### Function Docstrings
```python
def detect_with_annotated_image(
    model: YOLO,
    source: str | Path | np.ndarray,
    conf: float = 0.25,
    iou: float = 0.45,
    image_format: str = "JPEG",
) -> tuple[list[dict[str, int | str | float | dict[str, float]]], bytes]:
    """
    Perform detection and return both results and annotated image.
    
    This function runs YOLO inference on the provided image source and returns
    both structured detection data and an annotated image with bounding boxes.
    
    Args:
        model: Pre-loaded YOLO model instance
        source: Image source (file path, URL, or numpy array)
        conf: Confidence threshold (0.0-1.0, default: 0.25)
            Higher values = more certain detections, fewer false positives
        iou: IoU threshold for Non-Maximum Suppression (0.0-1.0, default: 0.45)
            Higher values = keep more overlapping boxes
        image_format: Output format for annotated image (JPEG, PNG, etc.)
    
    Returns:
        Tuple containing:
        - detection_results: List of detection dictionaries with:
            - index: Detection number (1-based)
            - class: Class name string
            - confidence: Detection confidence (0.0-1.0)
            - bbox: Bounding box dict with x1, y1, x2, y2
        - annotated_image_bytes: Image bytes with drawn bounding boxes
    
    Raises:
        Exception: If YOLO inference fails
    
    Example:
        >>> model = load_model("model/best.pt")
        >>> results, img_bytes = detect_with_annotated_image(
        ...     model, "image.jpg", conf=0.5
        ... )
        >>> print(f"Found {len(results)} detections")
    """
    # Implementation...
```

#### API Endpoint Documentation
```python
@app.post("/detect")
async def detect_traffic_signs(
    file: Annotated[UploadFile, File(description="Image file for detection")],
    conf: float = 0.25,
    iou: float = 0.45,
):
    """
    Detect traffic signs in uploaded image and return JSON results.
    
    This endpoint accepts an image file and returns structured detection data
    including class names, confidence scores, and bounding box coordinates.
    
    Args:
        file: Image file (JPEG, PNG, BMP, WebP, etc.)
        conf: Confidence threshold (0.0-1.0, default: 0.25)
        iou: IoU threshold for NMS (0.0-1.0, default: 0.45)
    
    Returns:
        JSON object with:
        - filename: Original filename
        - detections: Array of detection objects
        - detection_count: Total number of detections
    
    Raises:
        HTTPException: 400 if invalid file type
        HTTPException: 503 if model not loaded
        HTTPException: 500 if detection fails
    """
```

### README Updates

When adding features, update the README.md:
```markdown
## New Feature

Brief description of the feature.

### Usage

\```bash
# Example command
curl -X POST "http://localhost:8000/new-endpoint" ...
\```

### Response

\```json
{
  "result": "example"
}
\```
```

### API Documentation

#### Swagger/OpenAPI
- FastAPI automatically generates docs at `/docs`
- Use descriptive endpoint summaries and tags
- Include example request/response bodies

#### curl Examples
Always provide curl examples for each endpoint:
```bash
# Example format
curl -X POST "http://localhost:8000/endpoint?param=value" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@image.jpg" \
  -o output.jpg
```

## Language and Communication

### Code and Comments
- **Code**: English only
  - Variable names: `detection_results`, `confidence_threshold`
  - Function names: `detect_traffic_signs()`, `load_model()`
  - Comments: English explanations
  
### User-Facing Documentation
- **Primary**: Vietnamese (for README.md, user guides)
- **Secondary**: English (for API docs, technical docs)
- **Both**: Provide examples in both languages when possible

### Examples
```python
# Good: English code and comments
def calculate_iou(box1: list, box2: list) -> float:
    """Calculate Intersection over Union between two boxes."""
    # Calculate intersection area
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    # ... implementation
```

```markdown
<!-- Good: Vietnamese user documentation -->
# Hướng Dẫn Sử Dụng

## Cài Đặt
1. Clone repository
2. Cài đặt dependencies với `uv sync`

<!-- English technical docs -->
# API Reference

## POST /detect
Detect traffic signs in image...
```

## Technical Notes

### Model Information

#### YOLO Model Characteristics
- **Input**: RGB images (any size, auto-resized)
- **Output**: Bounding boxes, class probabilities, confidence scores
- **Classes**: Defined during training (check model.names for list)
- **Performance**: Real-time inference on GPU, slower on CPU

#### Understanding Thresholds

**Confidence Threshold (conf)**:
- Range: 0.0 to 1.0
- Purpose: Minimum confidence for a detection to be returned
- High (0.7-0.9): Only very certain detections, may miss objects
- Medium (0.4-0.6): Balanced precision and recall
- Low (0.1-0.3): More detections but more false positives
- Default: 0.25

**IoU Threshold (iou)**:
- Range: 0.0 to 1.0
- Purpose: Non-Maximum Suppression (NMS) threshold
- Use: Remove duplicate detections of same object
- High (0.6-0.9): Keep overlapping boxes (may show duplicates)
- Low (0.2-0.4): Aggressive removal (may lose legitimate detections)
- Default: 0.45

### System Requirements

#### Development
- **CPU**: Multi-core processor (Intel i5 or better)
- **RAM**: Minimum 8GB, recommended 16GB
- **Storage**: 2GB free space (model + dependencies)
- **OS**: Linux, macOS, or Windows
- **Python**: 3.12 or higher

#### Production
- **CPU**: 4+ cores for concurrent requests
- **RAM**: 16GB+ for multiple workers
- **GPU**: NVIDIA GPU with CUDA for faster inference (optional)
  - Reduces inference time from ~1s to ~50ms per image
- **Storage**: SSD recommended for faster model loading

### Troubleshooting

#### Model Loading Issues
```
Error: Model not loaded
Solution: Ensure backend/model/best.pt exists
```

#### Memory Errors
```
Error: Out of memory during inference
Solutions:
1. Reduce image size before processing
2. Increase system RAM
3. Use GPU inference (if available)
4. Process images sequentially, not in batch
```

#### CORS Errors
```
Error: CORS policy blocked
Solution: Check CORS middleware in main.py
- Development: allow_origins=["*"]
- Production: allow_origins=["https://yourdomain.com"]
```

#### Port Already in Use
```
Error: Address already in use
Solutions:
1. Change port: uvicorn main:app --port 8001
2. Kill existing process: lsof -ti:8000 | xargs kill
3. Use different port in docker: docker run -p 8001:8000
```

#### Frontend Not Loading
```
Issue: GET / returns JSON instead of HTML
Cause: Frontend path not found by FastAPI

Solution: Ensure frontend directory exists at correct location:

Docker Container (WORKDIR=/app/backend):
  - Checks: /app/backend/frontend (relative to WORKDIR)
  - Fallback: /app/frontend (parent dir, used in current Docker setup)
  - Frontend copied to: /app/frontend (see Dockerfile line 44)
  
Local Development:
  - Checks: backend/frontend (if running from backend/)
  - Fallback: ../frontend (if running from backend/, finds frontend/)
  - Or just ensure frontend/ exists next to backend/
```

## CI/CD Considerations

### Testing Strategy
```bash
# Unit tests for YOLO module
pytest backend/tests/test_yolo_module.py

# Integration tests for API
pytest backend/tests/test_api.py

# End-to-end tests
pytest backend/tests/test_e2e.py
```

### Build Pipeline
```yaml
# Example GitHub Actions
name: Build and Test
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: cd backend && uv sync
      - name: Run tests
        run: cd backend && uv run pytest
```

### Docker Build Optimization
```dockerfile
# Use BuildKit for better caching
DOCKER_BUILDKIT=1 docker build -t app .

# Multi-platform builds
docker buildx build --platform linux/amd64,linux/arm64 -t app .

# Cache mount for faster rebuilds
RUN --mount=type=cache,target=/root/.cache/uv uv sync
```

### Deployment Checklist
- [ ] Model file included in Docker image or mounted as volume
- [ ] Environment variables configured (if any)
- [ ] CORS origins restricted to production domains
- [ ] Health check endpoint responding
- [ ] Logging configured for production
- [ ] Resource limits set (CPU, memory)
- [ ] HTTPS configured (reverse proxy)
- [ ] Monitoring and alerting setup

## Best Practices Summary

### DO
✅ Use type hints everywhere
✅ Clean up temporary files in finally blocks
✅ Validate all inputs (file types, parameters)
✅ Use structured error messages
✅ Document all public functions and endpoints
✅ Use environment variables for configuration
✅ Test endpoints with both curl and Swagger UI
✅ Keep frontend simple (vanilla JS, no build tools)
✅ Use async/await for I/O operations
✅ Load model once at startup

### DON'T
❌ Store uploaded files permanently
❌ Hardcode configuration values
❌ Skip input validation
❌ Reload model on every request
❌ Return raw error stack traces to clients
❌ Use global mutable state (except for model)
❌ Add frontend build tools unnecessarily
❌ Commit secrets or API keys
❌ Run container as root user
❌ Allow unbounded file uploads
