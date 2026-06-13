# VisionVault 📦🔍

VisionVault is a high-performance, full-stack AI web application designed to automatically scan user-uploaded videos and generate highly accurate household inventory lists. By simply uploading a video walkthrough of a room or house, VisionVault uses state-of-the-art computer vision to identify, track, and count furniture, appliances, and decor.

## 🚀 Features
- **Zero-Shot YOLO-World AI**: Exclusively powered by the massive `yolov8x-worldv2.pt` model with a custom-tailored household vocabulary, completely eliminating false positives (like confusing white cabinets for refrigerators).
- **Dynamic Speed Limits**: Smart frame extraction logic caps video processing at a maximum of 60 evenly spaced frames. No matter how long a video is, processing guarantees an absolute maximum wait time of exactly 2 minutes without sacrificing end-to-end video coverage.
- **Flawless Object Tracking**: Reconstructed tracking aggregation prevents broken tracks from inflating item counts, ensuring zero duplicates in the final UI.
- **Asynchronous Processing**: Videos are processed in the background via Celery workers, ensuring the frontend API never blocks or crashes.

## 🛠️ Tech Stack
- **Frontend**: React + Vite (Interactive UI with beautiful glassmorphism design)
- **Backend**: Python + FastAPI (RESTful API endpoints)
- **Task Queue**: Celery + Redis (Asynchronous background video processing)
- **Storage**: MinIO (S3-compatible blob storage for video uploads)
- **Database**: PostgreSQL / SQLite (Job tracking and inventory storage)
- **AI / Computer Vision**: Ultralytics YOLO-World, OpenCV

## 📁 Project Structure
```text
VisionVault/
├── backend/
│   ├── api/            # FastAPI route endpoints
│   ├── scripts/        # Standalone utility & debugging scripts
│   ├── services/       # Core business logic (AI fusion, video extraction)
│   ├── weights/        # AI model files (e.g. yolov8x-worldv2.pt)
│   ├── worker/         # Celery task definitions
│   ├── config.py       # Global environment & configuration settings
│   └── main.py         # Application entry point
└── frontend/           # React + Vite user interface
```

## ⚙️ Getting Started

### 1. Prerequisites
Ensure you have the following installed on your machine:
- Node.js & npm
- Python 3.9+
- Docker Desktop (Required to run Redis & MinIO)

### 2. Start Dependencies (Redis & MinIO)
Run the required background services via Docker (ensure they are active before starting the backend).

### 3. Start the Backend API
Open a terminal and start the FastAPI server:
```bash
cd backend
python main.py
```
*(The backend will run at `http://localhost:8001`)*

### 4. Start the Celery Worker
Open a **new** terminal and start the asynchronous processing queue:
```bash
cd backend
celery -A worker.tasks worker --loglevel=info --pool=solo
```

### 5. Start the Frontend
Open a **new** terminal and launch the React application:
```bash
cd frontend
npm run dev
```
*(The frontend will run at `http://localhost:5173`)*

## 💡 Usage
1. Open your web browser and navigate to `http://localhost:5173`.
2. Click **"Upload Video"** and select any household video clip.
3. The video will be sent to the Celery worker for fast-forward AI extraction.
4. Watch as your final, perfect inventory populates on the screen automatically!
