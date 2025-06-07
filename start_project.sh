#!/bin/bash
# Script to start both frontend and backend for production environment

echo "===================================="
echo "   Starting project in production environment"
echo "===================================="

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
VENV_DIR="$SCRIPT_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Running build script..."
    bash "$SCRIPT_DIR/build.sh"
fi

# Check and stop running processes
echo "Checking and stopping running processes..."
pkill -f "node.*react-scripts" 2>/dev/null
pkill -f "python.*run.py" 2>/dev/null
pkill -f "gunicorn" 2>/dev/null

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Verify gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "Gunicorn not found. Installing..."
    pip install gunicorn
fi

# Get port from environment or use default
PORT=${PORT:-5001}
echo "Using port: $PORT"

# Start backend with Gunicorn in production
echo "Starting backend..."
cd "$BACKEND_DIR" || { echo "Backend directory not found!"; exit 1; }

# Start backend with Gunicorn
echo "Starting backend with Gunicorn..."
gunicorn -b 0.0.0.0:$PORT -w 4 run:app &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Start frontend
echo "Starting frontend..."
cd "$FRONTEND_DIR" || { echo "Frontend directory not found!"; exit 1; }

# Start frontend with serve
echo "Starting frontend with serve..."
npx serve -s build -l 3000 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

echo ""
echo "===================================="
echo "   Project started successfully!"
echo "   Backend: http://localhost:$PORT"
echo "   Frontend: http://localhost:3000"
echo "===================================="
echo ""
echo "Press Ctrl+C to stop all servers"

# Handle script cancellation
trap 'echo "Stopping servers..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT TERM

# Keep script running
wait