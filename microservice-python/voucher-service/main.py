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
    from controllers.voucher_controller import voucher_controller
    from routes.voucher_routes import router as voucher_router
    from shared.database import VoucherDatabase
    from shared.middleware import SecurityMiddleware, AuditMiddleware
    
    logger.info("✅ Successfully imported modules")
except Exception as e:
    logger.error(f"❌ Import error: {e}")
    raise

# Database lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Voucher Service...")
    
    # Connect to database
    success = await VoucherDatabase.connect()
    if not success:
        logger.error("❌ Failed to connect to database")
        raise Exception("Database connection failed")
    
    logger.info("✅ Voucher Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Voucher Service...")

# Create FastAPI app
app = FastAPI(
    title="Voux Voucher Service",
    description="Voucher Management Service for Voux Platform",
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
app.include_router(voucher_router, prefix="/api/vouchers", tags=["vouchers"])

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "Voucher Service is running",
        "timestamp": "2024-01-01T00:00:00Z",
        "features": ["Voucher Management", "Search", "Categories", "RBAC"]
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Voux Voucher Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("VOUCHER_SERVICE_PORT", 3003))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info"
    ) 