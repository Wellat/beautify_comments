#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ "$1" == "backend" ]; then
    echo "Starting Backend Service..."
    cd backend
    # Check if uvicorn is installed or accessible
    if command -v uvicorn &> /dev/null; then
        uvicorn main:app --reload --port 8080
    else
        echo "Error: uvicorn not found. Please ensure you have installed requirements.txt"
        echo "Try running: pip install -r backend/requirements.txt"
        exit 1
    fi

elif [ "$1" == "frontend" ]; then
    echo "Starting Frontend Service..."
    cd frontend
    # Check if npm is installed
    if command -v npm &> /dev/null; then
        npm run dev
    else
        echo "Error: npm not found. Please install Node.js"
        exit 1
    fi

else
    echo "Usage: $0 {backend|frontend}"
    echo "Examples:"
    echo "  $0 backend   # Start the FastAPI backend"
    echo "  $0 frontend  # Start the React frontend"
    exit 1
fi
