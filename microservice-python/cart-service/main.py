from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sys
import logging
from dotenv import load_dotenv

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.dirname(current_dir))  # Add parent dir

# Load environment variables
load_dotenv()

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple direct imports
try:
    from controllers.cart_controller import cart_controller
    from routes.cart_routes import router as cart_router
    from shared.database import CartDatabase
    from shared.middleware import SecurityMiddleware, AuditMiddleware
    
    logger.info("✅ Successfully imported modules")
except Exception as e:
    logger.error(f"❌ Import error: {e}")
    raise

# Database lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Cart Service...")
    
    # Connect to database
    success = await CartDatabase.connect()
    if not success:
        logger.error("❌ Failed to connect to database")
        raise Exception("Database connection failed")
    
    logger.info("✅ Cart Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Cart Service...")

# Create FastAPI app
app = FastAPI(
    title="Voux Cart Service",
    description="Shopping Cart Service for Voux Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://voux-platform.shop",
        "https://www.voux-platform.shop",
        "http://localhost:5173",
        "http://localhost:8060"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Security middleware
app.middleware("http")(SecurityMiddleware.add_security_headers)
app.middleware("http")(AuditMiddleware.audit_logger)

# Include routers
app.include_router(cart_router, prefix="/api/cart", tags=["cart"])

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "Cart Service is running",
        "timestamp": "2024-01-01T00:00:00Z",
        "features": ["Shopping Cart", "Cart Management", "Voucher Integration", "RBAC"]
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Voux Cart Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("CART_SERVICE_PORT", 3004))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info"
    ) 