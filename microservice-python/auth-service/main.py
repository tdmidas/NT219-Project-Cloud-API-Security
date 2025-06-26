from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, root_dir)

# Load environment variables
load_dotenv()

# Import local modules - using try/except for flexible imports
try:
    # Try relative imports first (when running as module)
    from .controllers.auth_controller import auth_controller
    from .routes.auth_routes import router as auth_router
    from ..shared.database import AuthDatabase
    from ..shared.middleware import SecurityMiddleware, AuditMiddleware
    from ..shared.event_manager import event_manager
except ImportError:
    try:
        # Try absolute imports from microservice-python directory
        from auth_service.controllers.auth_controller import auth_controller
        from auth_service.routes.auth_routes import router as auth_router
        from shared.database import AuthDatabase
        from shared.middleware import SecurityMiddleware, AuditMiddleware
        from shared.event_manager import event_manager
    except ImportError:
        # Final fallback - direct imports
        import sys
        auth_service_dir = os.path.join(parent_dir, 'auth-service')
        sys.path.append(auth_service_dir)
        
        from controllers.auth_controller import auth_controller
        from routes.auth_routes import router as auth_router
        from shared.database import AuthDatabase
        from shared.middleware import SecurityMiddleware, AuditMiddleware
        from shared.event_manager import event_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Auth Service...")
    
    # Connect to database
    success = await AuthDatabase.connect()
    if not success:
        logger.error("❌ Failed to connect to database")
        raise Exception("Database connection failed")
    
    # Connect to RabbitMQ for event publishing (non-blocking)
    try:
        rabbitmq_connected = await event_manager.connect()
        if rabbitmq_connected:
            logger.info("✅ RabbitMQ connected for event publishing")
        else:
            logger.warning("⚠️ RabbitMQ connection failed - events will be skipped")
    except Exception as e:
        logger.error(f"⚠️ RabbitMQ connection error: {e}")
        logger.info("🚀 Auth Service will continue without event publishing")
    
    logger.info("✅ Auth Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Auth Service...")
    try:
        await event_manager.disconnect()
    except Exception as e:
        logger.error(f"⚠️ Error disconnecting from RabbitMQ: {e}")

# Create FastAPI app
app = FastAPI(
    title="Voux Auth Service",
    description="Authentication and Authorization Service for Voux Platform",
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
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "Auth Service is running",
        "timestamp": "2024-01-01T00:00:00Z",
        "authentication": "JWT Authentication",
        "features": ["JWT Tokens", "Session Management", "RBAC", "OAuth Support"]
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Voux Auth Service",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("AUTH_SERVICE_PORT", 3001))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info"
    ) 