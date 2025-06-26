from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Voux API Gateway",
    description="Central API Gateway for Voux Microservices Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://voux-platform.shop",
        "https://www.voux-platform.shop",
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Service URLs
SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://localhost:3001"),
    "user": os.getenv("USER_SERVICE_URL", "http://localhost:3002"),
    "voucher": os.getenv("VOUCHER_SERVICE_URL", "http://localhost:3003"),
    "cart": os.getenv("CART_SERVICE_URL", "http://localhost:3004"),
}

# Service health status
service_health: Dict[str, bool] = {}

async def forward_request(service_url: str, path: str, method: str, request: Request) -> Response:
    """Forward request to microservice"""
    try:
        # Prepare request data
        headers = dict(request.headers)
        # Remove host header to avoid conflicts
        headers.pop("host", None)
        
        # Get request body if present
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        # Get query parameters
        params = dict(request.query_params)
        
        # Construct target URL
        target_url = f"{service_url}{path}"
        
        # Forward request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                content=body,
                params=params
            )
            
            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
            
    except httpx.TimeoutException:
        logger.error(f"Timeout forwarding {method} {path} to {service_url}")
        return JSONResponse(
            status_code=504,
            content={
                "success": False,
                "message": "Service timeout",
                "service": service_url
            }
        )
    except httpx.ConnectError:
        logger.error(f"Connection error forwarding {method} {path} to {service_url}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": "Service unavailable",
                "service": service_url
            }
        )
    except Exception as error:
        logger.error(f"Error forwarding {method} {path} to {service_url}: {error}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Gateway error",
                "error": str(error)
            }
        )

# Auth Service Routes
@app.api_route("/api/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def auth_service(path: str, request: Request):
    """Forward to Auth Service"""
    return await forward_request(SERVICES["auth"], f"/api/auth/{path}", request.method, request)

# User Service Routes
@app.api_route("/api/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def user_service(path: str, request: Request):
    """Forward to User Service"""
    return await forward_request(SERVICES["user"], f"/api/users/{path}", request.method, request)

# Voucher Service Routes
@app.api_route("/api/vouchers/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def voucher_service(path: str, request: Request):
    """Forward to Voucher Service"""
    return await forward_request(SERVICES["voucher"], f"/api/vouchers/{path}", request.method, request)

# Cart Service Routes
@app.api_route("/api/cart/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def cart_service(path: str, request: Request):
    """Forward to Cart Service"""
    return await forward_request(SERVICES["cart"], f"/api/cart/{path}", request.method, request)

# Health check for individual services
async def check_service_health(service_name: str, service_url: str) -> bool:
    """Check if a service is healthy"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_url}/health")
            return response.status_code == 200
    except:
        return False

# Gateway health check
@app.get("/health")
async def health_check():
    """Gateway health check"""
    # Check all services
    for service_name, service_url in SERVICES.items():
        service_health[service_name] = await check_service_health(service_name, service_url)
    
    all_healthy = all(service_health.values())
    
    return {
        "status": "Gateway is running",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": service_health,
        "all_services_healthy": all_healthy,
        "gateway_version": "1.0.0"
    }

# Service discovery endpoint
@app.get("/services")
async def service_discovery():
    """Get all available services"""
    return {
        "success": True,
        "services": SERVICES,
        "gateway": "http://localhost:8060",
        "available_routes": [
            "/api/auth/*",
            "/api/users/*", 
            "/api/vouchers/*",
            "/api/cart/*"
        ]
    }

# Load balancing status
@app.get("/status")
async def gateway_status():
    """Get gateway status and metrics"""
    # Check all services
    for service_name, service_url in SERVICES.items():
        service_health[service_name] = await check_service_health(service_name, service_url)
    
    healthy_services = sum(1 for status in service_health.values() if status)
    total_services = len(SERVICES)
    
    return {
        "success": True,
        "gateway": {
            "status": "running",
            "version": "1.0.0",
            "uptime": "N/A"  # Could implement actual uptime tracking
        },
        "services": {
            "total": total_services,
            "healthy": healthy_services,
            "unhealthy": total_services - healthy_services,
            "health_status": service_health
        },
        "features": [
            "Request Forwarding",
            "Service Discovery", 
            "Health Monitoring",
            "Load Balancing",
            "Error Handling"
        ]
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Voux API Gateway",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "services": "/services",
        "status_page": "/status"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": "Endpoint not found",
            "path": str(request.url.path),
            "available_routes": [
                "/api/auth/*",
                "/api/users/*", 
                "/api/vouchers/*",
                "/api/cart/*"
            ]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Handle 500 errors"""
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal gateway error",
            "error": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_GATEWAY_PORT", 8060))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
        log_level="info"
    ) 