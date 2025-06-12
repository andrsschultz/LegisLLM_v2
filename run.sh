#!/bin/bash

echo "Starting combined FastAPI + Streamlit application..."

# Start FastAPI backend in background on port 8000
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait a moment for backend to initialize
sleep 5

# Start Streamlit frontend on the PORT provided by Render
export BACKEND_URL=http://localhost:8000
streamlit run frontend/app.py \
  --server.port ${PORT:-8501} \
  --server.address 0.0.0.0 \
  --server.headless true \
  --server.runOnSave false \
  --server.fileWatcherType none \
  --server.enableCORS false \
  --server.enableXsrfProtection false
