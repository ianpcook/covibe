#!/bin/bash

# Agent Personality System - Startup Script
# This script starts both the backend API and frontend web interface

set -e  # Exit on any error

echo "🎭 Starting Agent Personality System..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down services...${NC}"
    
    # Kill background processes
    if [[ -n $BACKEND_PID ]]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Backend API stopped${NC}"
    fi
    
    if [[ -n $FRONTEND_PID ]]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✓ Frontend dev server stopped${NC}"
    fi
    
    echo -e "${GREEN}👋 Agent Personality System stopped${NC}"
    exit 0
}

# Set up cleanup trap
trap cleanup SIGINT SIGTERM EXIT

# Check if virtual environment exists
if [[ ! -d ".venv" ]]; then
    echo -e "${RED}❌ Virtual environment not found. Please run: python -m venv .venv && source .venv/bin/activate && pip install -e .${NC}"
    exit 1
fi

# Check if node_modules exists
if [[ ! -d "web/node_modules" ]]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    cd web && npm install && cd ..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
fi

echo -e "${BLUE}🚀 Starting backend API server...${NC}"

# Start backend API server
source .venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -c "
import uvicorn
from src.covibe.api.main import app
uvicorn.run(app, host='127.0.0.1', port=8000, log_level='info')
" &

BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${RED}❌ Backend API failed to start${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Backend API running at http://localhost:8000${NC}"
echo -e "${BLUE}  - API Documentation: http://localhost:8000/docs${NC}"
echo -e "${BLUE}  - Health Check: http://localhost:8000/health${NC}"
echo ""

echo -e "${BLUE}🎨 Starting frontend dev server...${NC}"

# Start frontend dev server
cd web
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 5

echo -e "${GREEN}✓ Frontend running at http://localhost:5173 (or next available port)${NC}"
echo ""

echo -e "${GREEN}🎉 Agent Personality System is ready!${NC}"
echo ""
echo -e "${YELLOW}Available services:${NC}"
echo -e "  🌐 Web Interface: http://localhost:5173"
echo -e "  🔧 API Server: http://localhost:8000"
echo -e "  📚 API Docs: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep script running and wait for user to stop
wait