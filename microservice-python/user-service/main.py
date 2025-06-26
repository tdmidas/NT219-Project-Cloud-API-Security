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
    from controllers.user_controller import user_controller
    from routes.user_routes import router as user_router
    from shared.database import UserDatabase
    from shared.middleware import SecurityMiddleware, AuditMiddleware
    from event_handlers import start_event_consumer
    
    logger.info("✅ Successfully imported modules")
except Exception as e:
    logger.error(f"❌ Import error: {e}")
    raise

# Database lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting User Service...")
    
    # Connect to database
    success = await UserDatabase.connect()
    if not success:
        logger.error("❌ Failed to connect to database")
        raise Exception("Database connection failed")
    
    # Start event consumer (non-blocking)
    try:
        import asyncio
        asyncio.create_task(start_event_consumer())
        logger.info("✅ Event consumer started")
    except Exception as e:
        logger.warning(f"⚠️ Event consumer failed to start: {e}")
        logger.info("🚀 User Service will continue without event processing")
    
    logger.info("✅ User Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down User Service...")

# Create FastAPI app
app = FastAPI(
    title="Voux User Service",
    description="User Management Service for Voux Platform",
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
app.include_router(user_router, prefix="/api/users", tags=["users"])

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "User Service is running",
        "timestamp": "2024-01-01T00:00:00Z",
        "features": ["User Management", "Profile Management", "RBAC", "Event Processing"]
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Voux User Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("USER_SERVICE_PORT", 3002))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info"
    ) 