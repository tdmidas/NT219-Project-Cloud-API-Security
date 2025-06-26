#!/usr/bin/env python3
"""
Run Voucher Service standalone
"""

import os
import sys
import uvicorn

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set working directory to voucher-service
voucher_service_dir = os.path.join(current_dir, "voucher-service")
os.chdir(voucher_service_dir)

if __name__ == "__main__":
    # Run with proper module path
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3003,
        reload=True,
        log_level="info"
    ) 