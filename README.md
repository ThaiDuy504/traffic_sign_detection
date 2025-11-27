# 🚦 Traffic Sign Detection System

Traffic sign detection project using YOLOv8 with FastAPI backend and user interface.

## 📋 Table of Contents

-   [Introduction](#-introduction)
-   [Features](#-features)
-   [Project Structure](#-project-structure)
-   [System Requirements](#-system-requirements)
-   [Installation](#-installation)
-   [Usage](#-usage)
-   [Docker Deployment](#-docker-deployment)
-   [API Documentation](#-api-documentation)
-   [Model Training](#-model-training)
-   [Technologies Used](#-technologies-used)

## 🎯 Introduction

Automatic traffic sign detection system using the YOLOv8 deep learning model. The project includes:

-   **Backend API**: FastAPI server providing endpoints for sign detection
-   **Frontend**: User interface for interacting with the system
-   **Training Notebook**: Jupyter notebook for training the YOLO model

## ✨ Features

-   🌐 **Modern Web Interface**: Upload images/videos and view results directly in the browser
-   🔍 Traffic sign detection in images with high accuracy
-   🎬 **Video Processing**: Detect traffic signs in video files
-   📷 **Real-time Detection**: Live detection via webcam streaming
-   📊 Returns detection results including: sign name, confidence, bounding box position
-   🖼️ Compare original and annotated images side-by-side
-   ⚙️ Adjust confidence and IoU thresholds in real-time
-   🚀 Simple and easy-to-use REST API
-   💪 Safe temporary file handling with automatic cleanup

## 📁 Project Structure

```
traffic_sign_detection/
├── backend/                 # FastAPI backend server
│   ├── model/              # Model weights directory
│   │   └── best.pt         # Trained YOLO model
│   ├── main.py             # FastAPI application
│   ├── yolo_module.py      # YOLO detection module
│   ├── pyproject.toml      # Backend dependencies
│   └── uv.lock            # Dependencies lock file
├── frontend/               # Web Frontend (HTML/CSS/JS)
│   ├── index.html         # Frontend UI
│   ├── style.css          # Styling
│   ├── script.js          # Frontend logic
│   └── README.md          # Frontend documentation
├── notebook/              # Training notebooks
│   └── train_yolo.ipynb   # YOLO training notebook
├── dockerfile             # Docker configuration
└── README.md              # This file
```

## 💻 System Requirements

-   Python >= 3.13
-   uv (Python package manager) or Docker
-   CUDA-compatible GPU (recommended for fast processing)
-   RAM >= 8GB
-   Disk space >= 2GB (for model and dependencies)

## 🚀 Installation

### 1. Install uv (if not available)

`uv` is a fast Python package manager. If you haven't installed it, use one of the following commands:

**macOS and Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Or install via pip:**

```bash
pip install uv
```

### 2. Install Backend

```bash
cd backend

# Install dependencies using uv (recommended)
uv sync
```

**Backend Dependencies:**

-   FastAPI >= 0.120.4 (with standard extras)
-   Ultralytics >= 8.3.223 (YOLOv8)
-   Uvicorn (included with FastAPI[standard])

### 3. Prepare Model

Ensure the `best.pt` model file is located in the `backend/model/` directory:

```
backend/model/best.pt
```

**Note:** The frontend is integrated with the backend, no separate installation is required.

## 🎮 Usage

### Start Server

```bash
cd backend

# Run with uvicorn
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or run directly
uv run main.py

# Or use python directly
python main.py
```

The server will start at: `http://localhost:8000`

### Use Web Interface

1. Start the server as instructed above
2. Open your browser and visit: `http://localhost:8000`
3. Select input mode: Image, Video, or Camera
4. Upload file or start camera
5. Adjust Confidence and IoU thresholds if needed
6. View detection results

### Health Check

```bash
curl http://localhost:8000/health
```

Response:

```json
{
    "status": "healthy",
    "model_loaded": true
}
```

## 🐳 Docker Deployment

### Build and Run Docker Container

```bash
# Build image
docker build -t traffic-sign-detection .

# Run container
docker run -p 8000:8000 traffic-sign-detection
```

The server will start at: `http://localhost:8000`

**Docker Notes:**

-   Dockerfile uses multi-stage build with Python 3.13-slim
-   Dependencies are installed via uv in the build stage
-   Runtime stage contains only essentials to reduce image size
-   Runs with non-root user (appuser) for better security
-   Frontend is copied directly into the container

## 📡 API Documentation

### Endpoints

#### 1. **GET /** - Frontend Interface

Access the web interface for uploading and detecting traffic signs.

Open browser and visit: `http://localhost:8000`

#### 2. **GET /health** - Health Check

Check server and model status.

**Response:**

```json
{
    "status": "healthy",
    "model_loaded": true
}
```

#### 3. **POST /detect** - Detect Signs (JSON Response)

Detect traffic signs and return results in JSON format.

**Parameters:**

-   `file` (required): Image file (JPEG, PNG, etc.)
-   `conf` (optional): Confidence threshold (0.0-1.0, default: 0.25)
-   `iou` (optional): IoU threshold for NMS (0.0-1.0, default: 0.45)

**Example Request (curl):**

```bash
curl -X POST "http://localhost:8000/detect?conf=0.5&iou=0.45" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/image.jpg"
```

**Example Response:**

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

#### 4. **POST /detect/image** - Detect Signs (Return Image)

Detect traffic signs and return the annotated image with bounding boxes.

**Parameters:**

-   `file` (required): Image file (JPEG, PNG, etc.)
-   `conf` (optional): Confidence threshold (0.0-1.0, default: 0.25)
-   `iou` (optional): IoU threshold for NMS (0.0-1.0, default: 0.45)

#### 5. **POST /detect/video** - Detect Signs (Video)

Detect traffic signs in a video file.

**Parameters:**

-   `file` (required): Video file (MP4, AVI, etc.)
-   `conf` (optional): Confidence threshold
-   `iou` (optional): IoU threshold

#### 6. **WS /ws/video/{session_id}** - Video Stream WebSocket

WebSocket endpoint for streaming processed video frames.

#### 7. **WS /ws** - Real-time WebSocket

WebSocket endpoint for real-time image processing (e.g., from camera).

### Swagger Documentation

Access interactive API docs at: `http://localhost:8000/docs`

## 🎓 Model Training

### Using Jupyter Notebook

1. Open training notebook:

```bash
cd notebook
jupyter notebook train_yolo.ipynb
```

2. Prepare dataset in YOLO format (see structure below)

3. Configure dataset path in the notebook

4. Run cells to train the model

5. Trained model (`best.pt`) will be saved and can be copied to `backend/model/`

### Dataset Structure

Dataset must follow YOLO format:

```
dataset/
├── train/
│   ├── images/
│   └── labels/
├── val/
│   ├── images/
│   └── labels/
└── data.yaml
```

## 🛠️ Technologies Used

### Backend

-   **FastAPI**: Modern, fast web framework for Python APIs
-   **Ultralytics YOLOv8**: State-of-the-art object detection model
-   **Uvicorn**: Lightning-fast ASGI server
-   **Pillow**: Image processing
-   **NumPy**: Numerical computations

### Model

-   **YOLOv8**: You Only Look Once version 8
-   **Framework**: PyTorch (via Ultralytics)

## 📝 Notes

-   `best.pt` model must be placed in `backend/model/` directory before running server
-   Server automatically loads model on startup (lifespan event)
-   Temporary files are automatically cleaned up after processing
-   Higher confidence threshold means more certainty but might miss some detections
-   IoU threshold is used for Non-Maximum Suppression to remove duplicate bounding boxes

## 🤝 Contribution

All contributions are welcome! Please create a pull request or open an issue to discuss.

## 📄 License

[Add your license info here]

## 👥 Author

[Add author info here]

---

**Happy Coding! 🚀**
