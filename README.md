# 🚦 Hệ Thống Phát Hiện Biển Báo Giao Thông

Dự án phát hiện biển báo giao thông sử dụng YOLOv8 với FastAPI backend và giao diện người dùng.

## 📋 Mục Lục

-   [Giới Thiệu](#-giới-thiệu)
-   [Tính Năng](#-tính-năng)
-   [Cấu Trúc Dự Án](#-cấu-trúc-dự-án)
-   [Yêu Cầu Hệ Thống](#-yêu-cầu-hệ-thống)
-   [Cài Đặt](#-cài-đặt)
-   [Sử Dụng](#-sử-dụng)
-   [Docker Deployment](#-docker-deployment)
-   [API Documentation](#-api-documentation)
-   [Huấn Luyện Model](#-huấn-luyện-model)
-   [Công Nghệ Sử Dụng](#-công-nghệ-sử-dụng)

## 🎯 Giới Thiệu

Hệ thống phát hiện biển báo giao thông tự động sử dụng mô hình deep learning YOLOv8. Dự án bao gồm:

-   **Backend API**: FastAPI server cung cấp endpoints để phát hiện biển báo
-   **Frontend**: Giao diện người dùng để tương tác với hệ thống
-   **Training Notebook**: Jupyter notebook để huấn luyện model YOLO

## ✨ Tính Năng

-   🌐 **Giao diện Web hiện đại**: Upload ảnh, video và xem kết quả trực tiếp trên trình duyệt
-   🔍 Phát hiện biển báo giao thông trong ảnh với độ chính xác cao
-   📊 Trả về kết quả phát hiện bao gồm: tên biển báo, độ tin cậy, vị trí bounding box
-   🖼️ So sánh ảnh gốc và ảnh đã được đánh dấu side-by-side
-   ⚙️ Tùy chỉnh ngưỡng confidence và IoU theo thời gian thực
-   🚀 API REST đơn giản và dễ sử dụng
-   💪 Xử lý ảnh tạm thời an toàn với tự động cleanup
-   🎬 **Xử lý video**: Upload video và nhận lại video đã được đánh dấu các biển báo
-   📷 **Camera real-time**: Phát hiện biển báo qua camera trực tiếp với WebSocket
-   🌐 **WebSocket streaming**: Xử lý video frame-by-frame với theo dõi tiến độ real-time
-   🗺️ **Mô tả tiếng Việt**: Hiển thị tên biển báo bằng tiếng Việt qua file class mapping

## 📁 Cấu Trúc Dự Án

```
traffic_sign_detection/
├── backend/                 # FastAPI backend server
│   ├── model/              # Thư mục chứa model weights
│   │   └── best.pt         # YOLO model đã được huấn luyện
│   ├── class_mapping.txt   # File ánh xạ mã biển báo sang tiếng Việt
│   ├── main.py             # FastAPI application
│   ├── yolo_module.py      # Module xử lý YOLO detection
│   ├── pyproject.toml      # Dependencies cho backend
│   └── uv.lock            # Lock file cho dependencies
├── frontend/               # Web Frontend (HTML/CSS/JS)
│   ├── index.html         # Frontend UI
│   ├── style.css          # Styling
│   ├── script.js          # Frontend logic
│   └── README.md          # Frontend documentation
├── notebook/              # Training notebooks
│   └── train_yolo.ipynb   # Notebook huấn luyện YOLO
├── dockerfile             # Docker configuration
└── README.md              # File này
```

## 💻 Yêu Cầu Hệ Thống

-   Python >= 3.13
-   uv (Python package manager) hoặc Docker
-   CUDA-compatible GPU (khuyến nghị cho tốc độ xử lý nhanh)
-   RAM >= 8GB
-   Disk space >= 2GB (cho model và dependencies)

## 🚀 Cài Đặt

### 1. Cài Đặt uv (nếu chưa có)

`uv` là một trình quản lý gói Python nhanh chóng. Nếu bạn chưa cài đặt, hãy sử dụng một trong các lệnh sau:

**macOS và Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Hoặc cài đặt qua pip:**

```bash
pip install uv
```

### 2. Cài Đặt Backend

```bash
cd backend

# Cài đặt dependencies bằng uv (khuyến nghị)
uv sync
```

**Dependencies Backend:**

-   FastAPI >= 0.120.4 (với standard extras)
-   Ultralytics >= 8.3.223 (YOLOv8)
-   Uvicorn (đi kèm với FastAPI[standard])

### 3. Chuẩn Bị Model

Đảm bảo file model `best.pt` nằm trong thư mục `backend/model/`:

```
backend/model/best.pt
```

**Lưu ý:** Frontend được tích hợp sẵn với backend, không cần cài đặt riêng.

## 🎮 Sử Dụng

### Khởi Động Server

```bash
cd backend

# Chạy với uvicorn
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Hoặc chạy trực tiếp
uv run main.py

# Hoặc sử dụng python trực tiếp
python main.py
```

Server sẽ khởi động tại: `http://localhost:8000`

### Sử Dụng Web Interface

1. Khởi động server như hướng dẫn ở trên
2. Mở trình duyệt và truy cập: `http://localhost:8000`
3. Chọn chế độ đầu vào:
    - **Image**: Chọn ảnh và xem kết quả phát hiện
    - **Video**: Upload video và xem video đã được đánh dấu
    - **Camera**: Bật camera để phát hiện biển báo real-time
4. Điều chỉnh ngưỡng Confidence và IoU nếu cần
5. Xem kết quả phát hiện với ảnh/video gốc và ảnh/video đã được đánh dấu

### Kiểm Tra Health Check

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

### Build và Chạy Docker Container

```bash
# Build image
docker build -t traffic-sign-detection .

# Chạy container
docker run -p 8000:8000 traffic-sign-detection
```

Server sẽ khởi động tại: `http://localhost:8000`

**Lưu ý Docker:**

-   Dockerfile sử dụng multi-stage build với Python 3.13-slim
-   Dependencies được cài đặt qua uv trong build stage
-   Runtime stage chỉ chứa những gì cần thiết để giảm image size
-   Chạy với non-root user (appuser) để bảo mật tốt hơn
-   Frontend được copy trực tiếp vào container

## 📡 API Documentation

### Endpoints

#### 1. **GET /** - Frontend Interface

Truy cập giao diện web để upload và phát hiện biển báo.

Mở trình duyệt và truy cập: `http://localhost:8000`

#### 2. **GET /health** - Health Check

Kiểm tra trạng thái server và model

**Response:**

```json
{
    "status": "healthy",
    "model_loaded": true
}
```

#### 3. **POST /detect** - Phát Hiện Biển Báo (JSON Response)

Phát hiện biển báo và trả về kết quả dạng JSON.

**Parameters:**

-   `file` (required): File ảnh (JPEG, PNG, etc.)
-   `conf` (optional): Ngưỡng confidence (0.0-1.0, mặc định: 0.25)
-   `iou` (optional): Ngưỡng IoU cho NMS (0.0-1.0, mặc định: 0.45)

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
            "class": "P.102",
            "class_name": "Cấm đi ngược chiều",
            "confidence": 0.95,
            "bbox": {
                "x1": 120.5,
                "y1": 80.3,
                "x2": 280.7,
                "y2": 240.9
            }
        },
        {
            "index": 2,
            "class": "P.127*60",
            "class_name": "Giới hạn tốc độ (60km/h)",
            "confidence": 0.87,
            "bbox": {
                "x1": 350.2,
                "y1": 100.5,
                "x2": 450.8,
                "y2": 200.1
            }
        }
    ],
    "detection_count": 2
}
```

**Lưu ý:** Trường `class_name` chứa mô tả tiếng Việt của biển báo (nếu có trong file `class_mapping.txt`).

#### 4. **POST /detect/image** - Phát Hiện Biển Báo (Trả Về Ảnh)

Phát hiện biển báo và trả về ảnh đã được đánh dấu bounding boxes.

**Parameters:**

-   `file` (required): File ảnh (JPEG, PNG, etc.)
-   `conf` (optional): Ngưỡng confidence (0.0-1.0, mặc định: 0.25)
-   `iou` (optional): Ngưỡng IoU cho NMS (0.0-1.0, mặc định: 0.45)

**Example Request (curl):**

```bash
curl -X POST "http://localhost:8000/detect/image?conf=0.5" \
  -H "accept: image/jpeg" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/image.jpg" \
  --output result.jpg
```

**Response:** Ảnh JPEG với các bounding boxes được vẽ lên các biển báo phát hiện được.

#### 5. **POST /detect/video** - Phát Hiện Biển Báo Trong Video

Phát hiện biển báo trong video và trả về video đã được đánh dấu.

**Parameters:**

-   `file` (required): File video (MP4, AVI, etc.)
-   `conf` (optional): Ngưỡng confidence (0.0-1.0, mặc định: 0.25)
-   `iou` (optional): Ngưỡng IoU cho NMS (0.0-1.0, mặc định: 0.45)

**Example Request (curl):**

```bash
curl -X POST "http://localhost:8000/detect/video?conf=0.5" \
  -H "accept: video/mp4" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/video.mp4" \
  --output annotated_video.mp4
```

**Response:** Video MP4 với các bounding boxes được vẽ lên các biển báo phát hiện được trong từng frame.

#### 6. **POST /detect/video/upload** - Upload Video Cho Streaming

Upload video và nhận session ID để xử lý streaming qua WebSocket.

**Parameters:**

-   `file` (required): File video (MP4, AVI, etc.)

**Example Request (curl):**

```bash
curl -X POST "http://localhost:8000/detect/video/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/video.mp4"
```

**Example Response:**

```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "total_frames": 300,
    "fps": 30,
    "filename": "video.mp4"
}
```

#### 7. **WebSocket /ws/video/{session_id}** - Video Streaming

Kết nối WebSocket để nhận video frames đã được xử lý theo thời gian thực.

**Query Parameters:**

-   `conf` (optional): Ngưỡng confidence (mặc định: 0.25)
-   `iou` (optional): Ngưỡng IoU (mặc định: 0.45)

**WebSocket URL:**

```
ws://localhost:8000/ws/video/{session_id}?conf=0.5&iou=0.45
```

**Messages:**

-   **Server → Client (JSON)**: Dữ liệu meta ban đầu `{"type": "metadata", "total_frames": 300, "fps": 30}`
-   **Server → Client (Binary)**: JPEG bytes của từng frame đã được annotate
-   **Server → Client (JSON)**: Hoàn thành `{"type": "done", "frames_processed": 300}`

#### 8. **WebSocket /ws** - Camera Real-time Detection

Kết nối WebSocket để phát hiện biển báo qua camera trực tiếp.

**Query Parameters:**

-   `conf` (optional): Ngưỡng confidence (mặc định: 0.25)
-   `iou` (optional): Ngưỡng IoU (mặc định: 0.45)

**WebSocket URL:**

```
ws://localhost:8000/ws?conf=0.5&iou=0.45
```

**Messages:**

-   **Client → Server (Binary)**: JPEG bytes của frame từ camera
-   **Server → Client (Binary)**: JPEG bytes của frame đã được annotate với bounding boxes

### Swagger Documentation

Truy cập interactive API docs tại: `http://localhost:8000/docs`

## 🎓 Huấn Luyện Model

### Sử dụng Jupyter Notebook

1. Mở notebook huấn luyện:

```bash
cd notebook
jupyter notebook train_yolo.ipynb
```

2. Chuẩn bị dataset theo format YOLO (xem cấu trúc bên dưới)

3. Cấu hình đường dẫn dataset trong notebook

4. Chạy các cell để huấn luyện model

5. Model sau khi huấn luyện (`best.pt`) sẽ được lưu và có thể copy vào `backend/model/`

### Cấu Trúc Dataset

Dataset cần tuân theo format YOLO:

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

## 🛠️ Công Nghệ Sử Dụng

### Backend

-   **FastAPI**: Modern, fast web framework cho Python APIs
-   **Ultralytics YOLOv8**: State-of-the-art object detection model
-   **Uvicorn**: Lightning-fast ASGI server
-   **OpenCV**: Video processing và image manipulation
-   **Pillow**: Image processing
-   **NumPy**: Numerical computations
-   **WebSocket**: Real-time camera streaming

### Model

-   **YOLOv8**: You Only Look Once version 8
-   **Framework**: PyTorch (thông qua Ultralytics)

## 📝 Lưu Ý

-   Model `best.pt` cần được đặt trong thư mục `backend/model/` trước khi chạy server
-   File `class_mapping.txt` chứa ánh xạ mã biển báo sang mô tả tiếng Việt (có thể tùy chỉnh)
-   Server sẽ tự động load model và class mapping khi khởi động (lifespan event)
-   Các file ảnh và video tạm thời được tự động cleanup sau khi xử lý
-   Confidence threshold càng cao thì kết quả càng chắc chắn nhưng có thể bỏ lỡ một số detection
-   IoU threshold dùng cho Non-Maximum Suppression để loại bỏ các bounding boxes trùng lặp
-   WebSocket camera yêu cầu trình duyệt hỗ trợ getUserMedia API
-   Video processing có thể mất nhiều thời gian tùy thuộc vào độ dài video
