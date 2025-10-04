#!/bin/bash

# Exoplanet Visualizer Startup Script
# This script starts both the backend and frontend servers

echo "🚀 Starting Exoplanet Visualizer..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0
    else
        return 1
    fi
}

# Check if backend is running
if check_port 8000; then
    echo -e "${GREEN}✓${NC} Backend is already running on port 8000"
else
    echo -e "${YELLOW}⚠${NC} Backend not running. Starting backend server..."
    cd "$PROJECT_ROOT/backend"
    python3 main.py &
    BACKEND_PID=$!
    sleep 3
    if check_port 8000; then
        echo -e "${GREEN}✓${NC} Backend started successfully (PID: $BACKEND_PID)"
    else
        echo "❌ Failed to start backend. Please check if Python and dependencies are installed."
        exit 1
    fi
fi

# Start frontend
echo ""
echo "Starting frontend development server..."
cd "$PROJECT_ROOT/frontend_2"

if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠${NC} Dependencies not installed. Running npm install..."
    npm install
fi

echo ""
echo -e "${GREEN}✓${NC} Starting frontend on http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the servers"
echo ""

npm run dev
