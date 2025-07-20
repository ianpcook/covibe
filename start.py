#!/usr/bin/env python3
"""
Agent Personality System - Startup Script
This script starts both the backend API and frontend web interface
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path


class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


class SystemManager:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        
    def log(self, message, color=Colors.NC):
        print(f"{color}{message}{Colors.NC}")
        
    def cleanup(self):
        """Stop all running processes"""
        self.running = False
        self.log("\n🛑 Shutting down services...", Colors.YELLOW)
        
        if self.backend_process:
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
                self.log("✓ Backend API stopped", Colors.GREEN)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                self.log("✓ Backend API force stopped", Colors.GREEN)
                
        if self.frontend_process:
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
                self.log("✓ Frontend dev server stopped", Colors.GREEN)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                self.log("✓ Frontend dev server force stopped", Colors.GREEN)
                
        self.log("👋 Agent Personality System stopped", Colors.GREEN)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.cleanup()
        sys.exit(0)
        
    def check_prerequisites(self):
        """Check if all prerequisites are met"""
        # Check virtual environment
        if not Path(".venv").exists():
            self.log("❌ Virtual environment not found.", Colors.RED)
            self.log("Please run: python -m venv .venv && source .venv/bin/activate && pip install -e .", Colors.RED)
            return False
            
        # Check node_modules
        if not Path("web/node_modules").exists():
            self.log("📦 Installing frontend dependencies...", Colors.YELLOW)
            try:
                subprocess.run(["npm", "install"], cwd="web", check=True)
                self.log("✓ Frontend dependencies installed", Colors.GREEN)
            except subprocess.CalledProcessError:
                self.log("❌ Failed to install frontend dependencies", Colors.RED)
                return False
                
        return True
        
    def start_backend(self):
        """Start the backend API server"""
        self.log("🚀 Starting backend API server...", Colors.BLUE)
        
        # Set up environment
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{env.get('PYTHONPATH', '')}:{os.getcwd()}"
        
        # Start backend process
        try:
            self.backend_process = subprocess.Popen([
                ".venv/bin/python", "-c",
                """
import uvicorn
from src.covibe.api.main import app
uvicorn.run(app, host='127.0.0.1', port=8000, log_level='info')
                """
            ], env=env)
            
            # Wait for backend to start
            time.sleep(3)
            
            # Check if backend is running
            try:
                import urllib.request
                import urllib.error
                
                response = urllib.request.urlopen("http://localhost:8000/health", timeout=5)
                if response.getcode() == 200:
                    self.log("✓ Backend API running at http://localhost:8000", Colors.GREEN)
                    self.log("  - API Documentation: http://localhost:8000/docs", Colors.BLUE)
                    self.log("  - Health Check: http://localhost:8000/health", Colors.BLUE)
                    return True
                else:
                    raise Exception("Health check failed")
            except Exception as e:
                self.log(f"❌ Backend API failed to start: {e}", Colors.RED)
                return False
                
        except Exception as e:
            self.log(f"❌ Failed to start backend: {e}", Colors.RED)
            return False
            
    def start_frontend(self):
        """Start the frontend dev server"""
        self.log("\n🎨 Starting frontend dev server...", Colors.BLUE)
        
        try:
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd="web"
            )
            
            # Wait for frontend to start
            time.sleep(5)
            
            self.log("✓ Frontend running at http://localhost:5173 (or next available port)", Colors.GREEN)
            return True
            
        except Exception as e:
            self.log(f"❌ Failed to start frontend: {e}", Colors.RED)
            return False
            
    def run(self):
        """Main execution function"""
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.log("🎭 Starting Agent Personality System...", Colors.GREEN)
        self.log("")
        
        # Check prerequisites
        if not self.check_prerequisites():
            sys.exit(1)
            
        # Start backend
        if not self.start_backend():
            sys.exit(1)
            
        # Start frontend
        if not self.start_frontend():
            sys.exit(1)
            
        # Show success message
        self.log("\n🎉 Agent Personality System is ready!", Colors.GREEN)
        self.log("")
        self.log("Available services:", Colors.YELLOW)
        self.log("  🌐 Web Interface: http://localhost:5173")
        self.log("  🔧 API Server: http://localhost:8000")
        self.log("  📚 API Docs: http://localhost:8000/docs")
        self.log("")
        self.log("Press Ctrl+C to stop all services", Colors.YELLOW)
        self.log("")
        
        # Keep running until interrupted
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()


if __name__ == "__main__":
    manager = SystemManager()
    manager.run()