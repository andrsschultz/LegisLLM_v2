#!/bin/bash

# Start FastAPI backend in the background
echo "Starting FastAPI backend..."
cd /opt/render/project/src
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 10

# Start Streamlit frontend
echo "Starting Streamlit frontend..."
export BACKEND_URL=http://localhost:8000
streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true --server.runOnSave false --server.fileWatcherType none
