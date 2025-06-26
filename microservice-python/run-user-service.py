#!/usr/bin/env python3
"""
Run User Service standalone
"""

import os
import sys
import uvicorn

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set working directory to user-service
user_service_dir = os.path.join(current_dir, "user-service")
os.chdir(user_service_dir)

if __name__ == "__main__":
    # Run with proper module path
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3002,
        reload=True,
        log_level="info"
    ) 