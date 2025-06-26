#!/usr/bin/env python3
"""
Run Cart Service standalone
"""

import os
import sys
import uvicorn

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set working directory to cart-service
cart_service_dir = os.path.join(current_dir, "cart-service")
os.chdir(cart_service_dir)

if __name__ == "__main__":
    # Run with proper module path
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3004,
        reload=True,
        log_level="info"
    ) 