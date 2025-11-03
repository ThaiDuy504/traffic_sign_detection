# GitHub Copilot Instructions for Traffic Sign Detection

## Project Overview

This is a Traffic Sign Detection system using YOLOv8 deep learning model with a FastAPI backend and frontend interface. The system can detect traffic signs in images with high accuracy and return results as JSON or annotated images.

## Tech Stack

### Backend
- **Python**: >= 3.12
- **FastAPI**: Modern web framework for building APIs (>= 0.120.4)
- **Ultralytics YOLOv8**: Object detection model (>= 8.3.223)
- **Uvicorn**: ASGI server
- **PIL (Pillow)**: Image processing
- **NumPy**: Array operations

### Package Management
- **uv**: Fast Python package manager (preferred)
- All dependencies managed via `pyproject.toml`

### Model
- **YOLOv8**: Deep learning model for real-time object detection
- Model weights stored in `backend/model/best.pt`

## Project Structure

```
traffic_sign_detection/
├── backend/                 # FastAPI backend server
│   ├── model/              # Model weights directory
│   │   └── best.pt         # Trained YOLO model
│   ├── main.py             # FastAPI application with endpoints
│   ├── yolo_module.py      # YOLO detection logic
│   ├── pyproject.toml      # Backend dependencies
│   └── .python-version     # Python version specification
├── frontend/               # Frontend application
│   ├── main.py            # Frontend entry point
│   └── pyproject.toml     # Frontend dependencies
├── notebook/              # Training notebooks
│   └── train_yolo.ipynb   # YOLO training notebook
└── README.md              # Project documentation
```

## Coding Conventions

### Python Style
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Use descriptive variable names
- Keep functions focused and single-purpose
- Use async/await for I/O operations in FastAPI

### Error Handling
- Use FastAPI's `HTTPException` for API errors
- Always clean up temporary files in `finally` blocks
- Validate input parameters (confidence, IoU thresholds)
- Check file types before processing

### API Patterns
- Use FastAPI's dependency injection for file uploads
- Return consistent JSON structures
- Include proper HTTP status codes
- Use `StreamingResponse` for image returns
- Implement health check endpoints

## Development Guidelines

### Adding New Features
1. **Model Changes**: Update `yolo_module.py` for detection logic
2. **API Endpoints**: Add to `main.py` following existing patterns
3. **Dependencies**: Add to `pyproject.toml`, then run `uv sync`

### Testing Endpoints
- Use the interactive docs at `http://localhost:8000/docs`
- Test with curl commands for automation
- Validate both JSON and image response formats

### Performance Considerations
- Use temporary files for image processing to avoid memory issues
- Always clean up temporary files after processing
- Set appropriate confidence and IoU thresholds
- Model loads once at startup (lifespan event)

### File Handling
- Accept standard image formats (JPEG, PNG)
- Use `tempfile.NamedTemporaryFile` for safe temporary storage
- Always validate `content_type` before processing
- Clean up with `Path.unlink(missing_ok=True)`

## API Design Patterns

### Endpoint Structure
```python
@app.post("/endpoint")
async def endpoint_name(
    file: Annotated[UploadFile, File(description="...")],
    param: type = default_value,
):
    """Clear docstring with Args and Returns"""
    # Validate model loaded
    # Validate inputs
    # Process with try/except/finally
    # Return structured response
```

### Response Formats
- **JSON Response**: Include filename, detections array, count
- **Detection Object**: index, class, confidence, bbox (x1, y1, x2, y2)
- **Image Response**: Use StreamingResponse with appropriate headers

## Common Tasks

### Running the Backend
```bash
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000
# OR
uv run main.py
```

### Adding Dependencies
```bash
cd backend  # or frontend
# Edit pyproject.toml to add dependency
uv sync  # Install dependencies
```

### Model Updates
- Replace `backend/model/best.pt` with new model
- Restart server to load new model
- Model is loaded once during startup via lifespan event

## Security Best Practices

- Validate file types before processing
- Use temporary files instead of storing uploads permanently
- Clean up all temporary files in finally blocks
- Set reasonable limits on file sizes
- Validate confidence and IoU threshold ranges (0.0-1.0)

## Documentation Standards

- Use docstrings for all functions
- Include Args and Returns sections
- Keep README.md updated with API changes
- Document all query parameters
- Provide curl examples for endpoints

## Language and Communication

- Primary language: Vietnamese (for user-facing docs)
- Code comments: English
- Variable/function names: English
- API documentation: Both Vietnamese and English examples

## Notes

- The model file (`best.pt`) must exist before starting the server
- Server will fail to start if model cannot be loaded
- All image processing uses temporary files for safety
- Confidence threshold: higher = more certain but may miss detections
- IoU threshold: used for Non-Maximum Suppression to remove overlapping boxes
