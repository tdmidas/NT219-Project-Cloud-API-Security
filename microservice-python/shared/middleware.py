from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any, Callable
import time
import logging
import asyncio
from datetime import datetime, timedelta
import os
import jwt
from .models.user import User
from .session_manager import session_manager
from .rbac import RBACManager, Permission

# Setup logging
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

# Rate limiting storage (in production, use Redis)
rate_limit_storage: Dict[str, List[float]] = {}

class SecurityMiddleware:
    """Security headers and general security middleware"""
    
    @staticmethod
    async def add_security_headers(request: Request, call_next):
        """Add security headers to responses"""
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Session-Security"] = "jwt-authentication-with-refresh"
        return response

class RateLimitMiddleware:
    """Rate limiting middleware"""
    
    @staticmethod
    def create_rate_limiter(max_requests: int = 100, window_minutes: int = 15, message: str = "Rate limit exceeded"):
        """Create a rate limiter function"""
        
        def rate_limiter(request: Request) -> bool:
            client_ip = request.client.host
            
            current_time = time.time()
            window_start = current_time - (window_minutes * 60)
            
            # Initialize storage for key if not exists
            if client_ip not in rate_limit_storage:
                rate_limit_storage[client_ip] = []
            
            # Remove old requests outside the window
            rate_limit_storage[client_ip] = [
                req_time for req_time in rate_limit_storage[client_ip] 
                if req_time > window_start
            ]
            
            # Check if limit exceeded
            if len(rate_limit_storage[client_ip]) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "success": False,
                        "message": message,
                        "retry_after": window_minutes * 60
                    }
                )
            
            # Add current request
            rate_limit_storage[client_ip].append(current_time)
            return True
            
        return rate_limiter

class AuthMiddleware:
    """Enhanced JWT Authentication middleware with session management"""
    
    def __init__(self):
        self.jwt_secret = os.getenv("JWT_ACCESS_KEY", "your-secret-key")
        self.jwt_algorithm = "HS256"
    
    async def verify_jwt_token(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
        """Verify JWT token with blacklist checking"""
        try:
            if not credentials or not credentials.credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Token required"
                    }
                )
            
            token = credentials.credentials
            
            # Check if token is blacklisted
            if session_manager.is_access_token_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Token đã bị thu hồi! Vui lòng đăng nhập lại.",
                        "error_code": "TOKEN_REVOKED",
                        "action_required": "LOGIN_AGAIN"
                    }
                )
            
            try:
                # Decode JWT token
                payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
                
                # Check token expiration
                if "exp" in payload:
                    if datetime.utcfromtimestamp(payload["exp"]) < datetime.utcnow():
                        raise jwt.ExpiredSignatureError()
                
                user_data = {
                    "id": payload.get("user_id"),
                    "username": payload.get("username"),
                    "rbac_role": payload.get("rbac_role", "USER"),
                    "auth_type": "jwt"
                }
                
                # Add RBAC info
                user_data["rbac_role"] = RBACManager.get_user_role(user_data)
                user_data["permissions"] = list(RBACManager.get_user_permissions(user_data))
                
                return user_data
                
            except jwt.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Phiên đăng nhập đã hết hạn! Vui lòng đăng nhập lại.",
                        "error_code": "TOKEN_EXPIRED",
                        "session_expired": True,
                        "action_required": "LOGIN_AGAIN"
                    }
                )
            except jwt.InvalidTokenError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Token không hợp lệ! Vui lòng đăng nhập lại.",
                        "error_code": "INVALID_TOKEN",
                        "action_required": "LOGIN_AGAIN"
                    }
                )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"JWT authentication failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Authentication failed",
                    "error": str(e)
                }
            )
    
    def generate_jwt_token(self, user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Generate JWT token"""
        try:
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(seconds=45)  # Default to 45 seconds (30s + 15s grace)
            
            payload = {
                "user_id": user_data.get("user_id"),
                "username": user_data.get("username"),
                "rbac_role": user_data.get("rbac_role", "USER"),
                "exp": expire,
                "iat": datetime.utcnow(),
                "token_type": "access"
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            return token
            
        except Exception as e:
            logger.error(f"JWT token generation failed: {e}")
            raise Exception("Failed to generate JWT token")

class PermissionMiddleware:
    """Permission-based access control middleware"""
    
    @staticmethod
    def require_permission(permission: Permission):
        """Middleware to require specific permission"""
        def permission_checker(current_user: Dict[str, Any] = Depends(lambda: None)):
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Authentication required"
                    }
                )
            
            if not RBACManager.has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "message": "Insufficient permissions",
                        "required_permission": permission.value,
                        "user_role": current_user.get("rbac_role"),
                        "user_permissions": current_user.get("permissions", [])
                    }
                )
            
            return current_user
        
        return permission_checker
    
    @staticmethod
    def require_resource_access(permission: Permission, ownership_permission: Optional[Permission] = None):
        """Middleware for resource-based access control"""
        def resource_checker(resource_id: str, current_user: Dict[str, Any] = Depends(lambda: None)):
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Authentication required"
                    }
                )
            
            if not RBACManager.can_access_resource(
                current_user, 
                resource_id, 
                permission, 
                ownership_permission
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "message": "Access denied - insufficient permissions or not resource owner",
                        "required_permission": permission.value,
                        "ownership_permission": ownership_permission.value if ownership_permission else None
                    }
                )
            
            return current_user
        
        return resource_checker

class AuditMiddleware:
    """Enhanced audit logging middleware"""
    
    @staticmethod
    async def audit_logger(request: Request, call_next):
        """Log requests for audit purposes with RBAC info"""
        start_time = time.time()
        
        # Extract user info if available
        user_info = {
            "type": "anonymous",
            "id": None,
            "role": "guest",
            "permissions": []
        }
        
        try:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                
                # Try to decode token for audit purposes (don't fail if invalid)
                try:
                    payload = jwt.decode(
                        token, 
                        os.getenv("JWT_ACCESS_KEY", "your-secret-key"), 
                        algorithms=["HS256"]
                    )
                    user_info = {
                        "type": "authenticated",
                        "id": payload.get("user_id"),
                        "username": payload.get("username"),
                        "rbac_role": payload.get("rbac_role", "USER")
                    }
                except:
                    user_info["type"] = "invalid_token"
        except:
            pass
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params),
            "ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "user": user_info
        }
        
        response = await call_next(request)
        
        # Add response info
        process_time = time.time() - start_time
        log_data.update({
            "status_code": response.status_code,
            "process_time": round(process_time, 4)
        })
        
        # Log with different levels based on status
        if response.status_code >= 400:
            logger.warning(f"🚨 [AUDIT] {log_data}")
        else:
            logger.info(f"📝 [AUDIT] {log_data}")
        
        return response

# Dependency functions
auth_middleware = AuthMiddleware()

# Enhanced authentication dependencies
async def get_current_user(user: Dict[str, Any] = Depends(auth_middleware.verify_jwt_token)) -> Dict[str, Any]:
    """Get current authenticated user with RBAC info"""
    return user

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        request = None  # Mock request for now
        return await auth_middleware.verify_jwt_token(request, credentials)
    except:
        return None

def require_admin() -> Dict[str, Any]:
    """Require admin privileges"""
    def check_admin(current_user: Dict[str, Any] = Depends(get_current_user)):
        if not RBACManager.has_permission(current_user, Permission.ADMIN_ACCESS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Admin access required",
                    "user_role": current_user.get("rbac_role")
                }
            )
        return current_user
    
    return check_admin

def require_permission_dep(permission: Permission):
    """FastAPI dependency for permission checking"""
    def check_permission(current_user: Dict[str, Any] = Depends(get_current_user)):
        if not RBACManager.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Insufficient permissions",
                    "required_permission": permission.value,
                    "user_permissions": current_user.get("permissions", [])
                }
            )
        return current_user
    
    return check_permission

# Rate limiting dependencies with different levels
strict_rate_limit = RateLimitMiddleware.create_rate_limiter(10, 15, "Strict API rate limit exceeded")
normal_rate_limit = RateLimitMiddleware.create_rate_limiter(50, 15, "API rate limit exceeded")
public_rate_limit = RateLimitMiddleware.create_rate_limiter(100, 15, "Public API rate limit exceeded")
auth_rate_limit = RateLimitMiddleware.create_rate_limiter(5, 15, "Authentication rate limit exceeded")