#!/bin/bash

# Create and activate virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install frontend dependencies and serve
echo "Installing frontend dependencies..."
cd frontend
npm install
npm install serve
npm run build
cd ..

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p backend/static
mkdir -p backend/templates

# Copy frontend build to backend static directory
echo "Copying frontend build to backend..."
cp -r frontend/build/* backend/static/

echo "Build completed successfully!" 