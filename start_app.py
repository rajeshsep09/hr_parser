#!/usr/bin/env python3
"""
Simple script to start the HR Parser application.
This script sets up the Python path and starts the FastAPI server.
"""

import sys
import os
import subprocess

# Add src directory to Python path
src_dir = os.path.join(os.path.dirname(__file__), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

if __name__ == "__main__":
    # Start the FastAPI server
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "src.app.main:app", 
        "--reload", 
        "--port", "8080"
    ])
