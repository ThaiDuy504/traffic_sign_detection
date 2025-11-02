# 🚦 Hệ Thống Phát Hiện Biển Báo Giao Thông

Dự án phát hiện biển báo giao thông sử dụng YOLOv8 với FastAPI backend và giao diện người dùng.

## 📋 Mục Lục

- [Giới Thiệu](#giới-thiệu)
- [Tính Năng](#tính-năng)
- [Cấu Trúc Dự Án](#cấu-trúc-dự-án)
- [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
- [Cài Đặt](#cài-đặt)
- [Sử Dụng](#sử-dụng)
- [API Documentation](#api-documentation)
- [Huấn Luyện Model](#huấn-luyện-model)
- [Công Nghệ Sử Dụng](#công-nghệ-sử-dụng)

## 🎯 Giới Thiệu

Hệ thống phát hiện biển báo giao thông tự động sử dụng mô hình deep learning YOLOv8. Dự án bao gồm:
- **Backend API**: FastAPI server cung cấp endpoints để phát hiện biển báo
- **Frontend**: Giao diện người dùng để tương tác với hệ thống
- **Training Notebook**: Jupyter notebook để huấn luyện model YOLO

## ✨ Tính Năng

- 🔍 Phát hiện biển báo giao thông trong ảnh với độ chính xác cao
- 📊 Trả về kết quả phát hiện bao gồm: tên biển báo, độ tin cậy, vị trí bounding box
- 🖼️ Xuất ảnh đã được đánh dấu các biển báo phát hiện được
- ⚙️ Tùy chỉnh ngưỡng confidence và IoU
- 🚀 API REST đơn giản và dễ sử dụng
- 💪 Xử lý ảnh tạm thời an toàn với tự động cleanup

## 📁 Cấu Trúc Dự Án

```
traffic_sign_detection/
├── backend/                 # FastAPI backend server
│   ├── model/              # Thư mục chứa model weights
│   │   └── best.pt         # YOLO model đã được huấn luyện
│   ├── main.py             # FastAPI application
│   ├── yolo_module.py      # Module xử lý YOLO detection
│   ├── pyproject.toml      # Dependencies cho backend
│   └── .python-version     # Python version
├── frontend/               # Frontend application
│   ├── main.py            # Frontend entry point
│   └── pyproject.toml     # Dependencies cho frontend
├── notebook/              # Training notebooks
│   ├── train_yolo.ipynb   # Notebook huấn luyện YOLO
│   └── yolo_dataset.zip   # Dataset cho training
└── README.md              # File này
```

## 💻 Yêu Cầu Hệ Thống

- Python >= 3.12
- CUDA-compatible GPU (khuyến nghị cho tốc độ xử lý nhanh)
- RAM >= 8GB
- Disk space >= 2GB (cho model và dependencies)

## 🚀 Cài Đặt

### 1. Clone Repository

```bash
cd traffic_sign_detection
```

### 2. Cài Đặt Backend

```bash
cd backend

# Cài đặt dependencies bằng uv (khuyến nghị)
uv sync

```

**Dependencies Backend:**
- FastAPI >= 0.120.4 (với standard extras)
- Ultralytics >= 8.3.223 (YOLOv8)
- Uvicorn (đi kèm với FastAPI[standard])

### 3. Chuẩn Bị Model

Đảm bảo file model `best.pt` nằm trong thư mục `backend/model/`:
```
backend/model/best.pt
```

### 4. Cài Đặt Frontend (Tùy Chọn)

```bash
cd frontend
uv sync
```

## 🎮 Sử Dụng

### Khởi Động Backend Server

```bash
cd backend

# Chạy với uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000

# Hoặc chạy trực tiếp
uv run main.py
```

Server sẽ khởi động tại: `http://localhost:8000`

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

## 📡 API Documentation

### Endpoints

#### 1. **GET /** - Root Endpoint
Kiểm tra API đang chạy

**Response:**
```json
{
  "message": "Traffic Sign Detection API",
  "status": "running",
  "endpoints": {
    "detect": "/detect",
    "health": "/health"
  }
}
```

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
- `file` (required): File ảnh (JPEG, PNG, etc.)
- `conf` (optional): Ngưỡng confidence (0.0-1.0, mặc định: 0.25)
- `iou` (optional): Ngưỡng IoU cho NMS (0.0-1.0, mặc định: 0.45)

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
    },
    {
      "index": 2,
      "class": "speed_limit_60",
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

#### 4. **POST /detect/image** - Phát Hiện Biển Báo (Trả Về Ảnh)

Phát hiện biển báo và trả về ảnh đã được đánh dấu bounding boxes.

**Parameters:**
- `file` (required): File ảnh (JPEG, PNG, etc.)
- `conf` (optional): Ngưỡng confidence (0.0-1.0, mặc định: 0.25)
- `iou` (optional): Ngưỡng IoU cho NMS (0.0-1.0, mặc định: 0.45)

**Example Request (curl):**
```bash
curl -X POST "http://localhost:8000/detect/image?conf=0.5" \
  -H "accept: image/jpeg" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/image.jpg" \
  --output result.jpg
```

**Response:** Ảnh JPEG với các bounding boxes được vẽ lên các biển báo phát hiện được.

### Swagger Documentation

Truy cập interactive API docs tại: `http://localhost:8000/docs`

## 🎓 Huấn Luyện Model

### Sử dụng Jupyter Notebook

1. Mở notebook huấn luyện:
```bash
cd notebook
jupyter notebook train_yolo.ipynb
```

2. Dataset được đóng gói trong `yolo_dataset.zip`

3. Giải nén dataset và cấu hình đường dẫn trong notebook

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
- **FastAPI**: Modern, fast web framework cho Python APIs
- **Ultralytics YOLOv8**: State-of-the-art object detection model
- **Uvicorn**: Lightning-fast ASGI server
- **Pillow**: Image processing
- **NumPy**: Numerical computations

### Model
- **YOLOv8**: You Only Look Once version 8
- **Framework**: PyTorch (thông qua Ultralytics)

## 📝 Lưu Ý

- Model `best.pt` cần được đặt trong thư mục `backend/model/` trước khi chạy server
- Server sẽ tự động load model khi khởi động (lifespan event)
- Các file ảnh tạm thời được tự động cleanup sau khi xử lý
- Confidence threshold càng cao thì kết quả càng chắc chắn nhưng có thể bỏ lỡ một số detection
- IoU threshold dùng cho Non-Maximum Suppression để loại bỏ các bounding boxes trùng lặp

## 🤝 Đóng Góp

Mọi đóng góp đều được chào đón! Hãy tạo pull request hoặc mở issue để thảo luận.

## 📄 License

[Thêm thông tin license của bạn ở đây]

## 👥 Tác Giả

[Thêm thông tin tác giả ở đây]

---

**Happy Coding! 🚀**
