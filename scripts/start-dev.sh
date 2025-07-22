#!/bin/bash

# Start both frontend and backend for development
# This script starts both services in the background

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python and uv
    if ! command -v uv &> /dev/null; then
        log_error "uv is not installed. Install with: pip install uv"
        exit 1
    fi
    
    # Check Node.js and npm
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed. Install Node.js from https://nodejs.org/"
        exit 1
    fi
    
    # Check if we're in the right directory
    if [[ ! -f "pyproject.toml" ]]; then
        log_error "pyproject.toml not found. Are you in the project root?"
        exit 1
    fi
    
    if [[ ! -f "web/package.json" ]]; then
        log_error "web/package.json not found. Frontend directory missing?"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    
    # Install backend dependencies
    log_info "Installing backend dependencies..."
    uv sync
    
    # Install frontend dependencies
    log_info "Installing frontend dependencies..."
    cd web
    npm install
    cd ..
    
    log_success "Dependencies installed"
}

# Start backend
start_backend() {
    log_info "Starting backend server..."
    
    # Create data directory
    mkdir -p data logs
    
    # Check if port 8000 is available
    log_info "Checking if port 8000 is available..."
    if lsof -ti:8000 >/dev/null 2>&1; then
        log_warning "Port 8000 is in use. Attempting to free it..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        sleep 2
        
        # Check again
        if lsof -ti:8000 >/dev/null 2>&1; then
            log_error "Port 8000 is still in use. Please free it manually: lsof -ti:8000 | xargs kill -9"
            return 1
        fi
    fi
    
    # Start backend in background
    log_info "Starting uvicorn server..."
    uv run uvicorn src.covibe.api.main:app --reload --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > .backend.pid
    
    # Wait for backend to start
    log_info "Waiting for backend to start..."
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &>/dev/null; then
            log_success "Backend started successfully on http://localhost:8000"
            return 0
        fi
        
        # Check if the process is still running
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            log_error "Backend process died. Check logs/backend.log for details:"
            tail -10 logs/backend.log
            return 1
        fi
        
        sleep 1
    done
    
    log_error "Backend failed to start within 30 seconds"
    log_info "Backend logs:"
    tail -10 logs/backend.log
    return 1
}

# Start frontend
start_frontend() {
    log_info "Starting frontend server..."
    
    cd web
    # Start frontend in background
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../.frontend.pid
    cd ..
    
    # Wait for frontend to start
    log_info "Waiting for frontend to start..."
    for i in {1..30}; do
        if curl -f http://localhost:5173 &>/dev/null || curl -f http://localhost:3000 &>/dev/null; then
            log_success "Frontend started successfully"
            return 0
        fi
        sleep 1
    done
    
    log_warning "Frontend may still be starting (check logs/frontend.log)"
    return 0
}

# Stop services
stop_services() {
    log_info "Stopping services..."
    
    # Stop backend using PID file
    if [[ -f .backend.pid ]]; then
        BACKEND_PID=$(cat .backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            sleep 2
            # Force kill if still running
            if kill -0 $BACKEND_PID 2>/dev/null; then
                kill -9 $BACKEND_PID 2>/dev/null || true
            fi
            log_info "Backend stopped (PID: $BACKEND_PID)"
        fi
        rm -f .backend.pid
    fi
    
    # Stop frontend using PID file
    if [[ -f .frontend.pid ]]; then
        FRONTEND_PID=$(cat .frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            sleep 2
            # Force kill if still running
            if kill -0 $FRONTEND_PID 2>/dev/null; then
                kill -9 $FRONTEND_PID 2>/dev/null || true
            fi
            log_info "Frontend stopped (PID: $FRONTEND_PID)"
        fi
        rm -f .frontend.pid
    fi
    
    # Kill any remaining uvicorn processes
    log_info "Killing any remaining backend processes..."
    pkill -f "uvicorn.*src.covibe.api.main:app" 2>/dev/null || true
    pkill -f "uvicorn src.covibe.api.main:app" 2>/dev/null || true
    pkill -f "python.*uvicorn.*main:app" 2>/dev/null || true
    
    # Kill any remaining npm dev processes
    log_info "Killing any remaining frontend processes..."
    pkill -f "npm run dev" 2>/dev/null || true
    pkill -f "vite.*dev" 2>/dev/null || true
    
    # Kill processes using ports 8000 and 5173
    log_info "Freeing up ports 8000 and 5173..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    
    # Wait a moment and verify
    sleep 1
    
    # Check if backend is still running
    if curl -f http://localhost:8000/health &>/dev/null; then
        log_warning "Backend may still be running - try manually: lsof -ti:8000 | xargs kill -9"
    else
        log_success "Backend stopped"
    fi
    
    # Check if frontend is still running
    if curl -f http://localhost:5173 &>/dev/null || curl -f http://localhost:3000 &>/dev/null; then
        log_warning "Frontend may still be running - try manually: lsof -ti:5173 | xargs kill -9"
    else
        log_success "Frontend stopped"
    fi
    
    log_success "Services stopped"
}

# Show status
show_status() {
    log_info "Service status:"
    
    # Check backend
    if curl -f http://localhost:8000/health &>/dev/null; then
        log_success "Backend: Running on http://localhost:8000"
        echo "  - API Docs: http://localhost:8000/docs"
        echo "  - Health: http://localhost:8000/health"
    else
        log_error "Backend: Not running"
    fi
    
    # Check frontend
    if curl -f http://localhost:5173 &>/dev/null; then
        log_success "Frontend: Running on http://localhost:5173"
    elif curl -f http://localhost:3000 &>/dev/null; then
        log_success "Frontend: Running on http://localhost:3000"
    else
        log_warning "Frontend: Not running or still starting"
    fi
}

# Show logs
show_logs() {
    log_info "Recent logs:"
    
    if [[ -f logs/backend.log ]]; then
        echo -e "${BLUE}=== Backend Logs ===${NC}"
        tail -20 logs/backend.log
    fi
    
    if [[ -f logs/frontend.log ]]; then
        echo -e "${BLUE}=== Frontend Logs ===${NC}"
        tail -20 logs/frontend.log
    fi
}

# Main function
main() {
    case "${1:-start}" in
        start)
            check_prerequisites
            install_dependencies
            start_backend
            start_frontend
            echo
            log_success "Both services started!"
            show_status
            echo
            log_info "To stop services: $0 stop"
            log_info "To check status: $0 status"
            log_info "To view logs: $0 logs"
            ;;
        stop)
            stop_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        restart)
            stop_services
            sleep 2
            main start
            ;;
        *)
            echo "Usage: $0 {start|stop|status|logs|restart}"
            echo
            echo "Commands:"
            echo "  start   - Start both backend and frontend"
            echo "  stop    - Stop both services"
            echo "  status  - Check service status"
            echo "  logs    - Show recent logs"
            echo "  restart - Restart both services"
            exit 1
            ;;
    esac
}

# Handle Ctrl+C
trap 'stop_services; exit 0' INT TERM

# Run main function
main "$@"