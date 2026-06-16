FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV and AI models
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Expose port for FastAPI
EXPOSE 8001

# Start script will be handled by Render (either uvicorn or celery)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
