# Vehicle Detection Frontend

Simple web interface for vehicle and license plate detection.

## Features

- Upload images for vehicle detection
- Adjust confidence and IoU thresholds in real-time
- View original and annotated images side-by-side
- See detailed detection results with bounding boxes

## Running the Application

1. Start the backend server:
```bash
cd backend
python main.py
```

2. Open your browser and go to:
```
http://localhost:8000
```

That's it! The frontend is served directly by the FastAPI backend.

## API Endpoints

- `GET /` - Frontend interface
- `POST /detect` - Get detection results (JSON)
- `POST /detect/image` - Get annotated image
- `GET /health` - Health check

