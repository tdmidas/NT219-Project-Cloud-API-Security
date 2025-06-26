from fastapi import APIRouter, HTTPException, Request, Depends, Response
from fastapi.responses import JSONResponse
from datetime import datetime
import os

# Flexible imports
try:
    # Try relative imports first (when running as module)
    from ..controllers.auth_controller import (
        auth_controller, 
        LoginRequest, 
        LogoutRequest,
        RefreshTokenRequest,
        ChangePasswordRequest
    )
    from ...shared.models.user import UserCreate
    from ...shared.middleware import (
        get_current_user, 
        get_current_user_optional,
        require_admin,
        require_permission_dep,
        normal_rate_limit,
        strict_rate_limit,
        auth_rate_limit
    )
    from ...shared.rbac import Permission
except ImportError:
    # Fallback to absolute imports (when running directly)
    from controllers.auth_controller import (
        auth_controller, 
        LoginRequest, 
        LogoutRequest,
        RefreshTokenRequest,
        ChangePasswordRequest
    )
    from shared.models.user import UserCreate
    from shared.middleware import (
        get_current_user, 
        get_current_user_optional,
        require_admin,
        require_permission_dep,
        normal_rate_limit,
        strict_rate_limit,
        auth_rate_limit
    )
    from shared.rbac import Permission

router = APIRouter()

# Cookie settings based on environment
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"
SECURE_COOKIES = IS_PRODUCTION  # Only secure in production

# Public endpoints

# Registration endpoint
@router.post("/register")
async def register(user_data: UserCreate):
    """User registration without rate limiting for testing"""
    return await auth_controller.register(user_data)

# Login endpoint
@router.post("/login")
async def login(login_data: LoginRequest, request: Request, response: Response):
    """Enhanced login with session management - no rate limiting for testing"""
    result = await auth_controller.login(login_data, request)
    
    if result.get("success") and result.get("refresh_token"):
        # Set refresh token as HTTP-only cookie
        max_age = 2592000 if login_data.remember_me else 604800  # 30 days or 7 days
        
        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            max_age=max_age,
            httponly=True,  # HTTP-only cookie
            secure=SECURE_COOKIES,    # Only secure in production
            samesite="strict"  # CSRF protection
        )
        
        # Remove refresh_token from response body
        result.pop("refresh_token", None)
        
        print(f"✅ Set refresh token as HTTP-only cookie for user: {login_data.username} (secure: {SECURE_COOKIES})")
    
    return result

# Token refresh endpoint (public but requires valid refresh token)
@router.post("/refresh", dependencies=[Depends(normal_rate_limit)])
async def refresh_token(request: Request, response: Response):
    """Refresh access token using refresh token from HTTP-only cookie"""
    
    # Get refresh token from HTTP-only cookie
    refresh_token = request.cookies.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "message": "Refresh token không tồn tại hoặc đã hết hạn!"
            }
        )
    
    # Create refresh request object
    refresh_request = RefreshTokenRequest(refresh_token=refresh_token)
    result = await auth_controller.refresh_token(refresh_request, request)
    
    if result.get("success") and result.get("refresh_token"):
        # Set new refresh token as HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            max_age=600,  # 10 minutes (same as refresh_expires_in)
            httponly=True,
            secure=SECURE_COOKIES,
            samesite="strict"
        )
        
        # Remove refresh_token from response body
        result.pop("refresh_token", None)
        
        print(f"✅ Set new refresh token as HTTP-only cookie (secure: {SECURE_COOKIES})")
    
    return result

# Verify token endpoint (public)
@router.post("/verify", dependencies=[Depends(normal_rate_limit)])
async def verify_token(token: str):
    """Verify JWT token validity"""
    return auth_controller.verify_token(token)

# Protected endpoints (require authentication)

# Logout endpoint
@router.post("/logout", dependencies=[Depends(normal_rate_limit)])
async def logout(
    request: Request, 
    response: Response,
    logout_data: LogoutRequest = LogoutRequest(),
    current_user: dict = Depends(get_current_user_optional)
):
    """Enhanced logout with token revocation"""
    result = await auth_controller.logout(request, logout_data, current_user)
    
    # Clear refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=SECURE_COOKIES,
        samesite="strict"
    )
    
    print(f"✅ Cleared refresh token cookie for user: {current_user.get('username', 'unknown') if current_user else 'unknown'} (secure: {SECURE_COOKIES})")
    
    return result

# Profile endpoint
@router.get("/profile", dependencies=[Depends(get_current_user)])
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get user profile with RBAC information"""
    return await auth_controller.get_profile(current_user)

# Change password endpoint
@router.post("/change-password", dependencies=[Depends(get_current_user), Depends(strict_rate_limit)])
async def change_password(
    password_request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    """Change user password (forces logout from all sessions)"""
    return await auth_controller.change_password(password_request, current_user)

# Session management endpoints

# Get user sessions
@router.get("/sessions", dependencies=[Depends(require_permission_dep(Permission.MANAGE_OWN_SESSIONS))])
async def get_user_sessions(current_user: dict = Depends(get_current_user)):
    """Get user's active sessions"""
    return await auth_controller.get_user_sessions(current_user)

# Revoke all sessions (force logout from all devices)
@router.post("/sessions/revoke-all", dependencies=[Depends(require_permission_dep(Permission.MANAGE_OWN_SESSIONS)), Depends(strict_rate_limit)])
async def revoke_all_sessions(current_user: dict = Depends(get_current_user)):
    """Revoke all user sessions (logout from all devices)"""
    from ...shared.session_manager import session_manager
    
    success = await session_manager.revoke_all_user_tokens(current_user.get("id"))
    
    if success:
        return {
            "success": True,
            "message": "Đã đăng xuất khỏi tất cả thiết bị! 🔐"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Lỗi khi thu hồi phiên!"
            }
        )

# Admin endpoints

# Get all user sessions (admin only)
@router.get("/admin/sessions", dependencies=[Depends(require_permission_dep(Permission.MANAGE_ALL_SESSIONS))])
async def admin_get_all_sessions(current_user: dict = Depends(get_current_user)):
    """Get all user sessions (admin only)"""
    from ...shared.database import AuthDatabase
    from ...shared.session_manager import session_manager
    
    try:
        refresh_tokens_collection = AuthDatabase.get_collection("refresh_tokens")
        
        # Get all active sessions
        sessions = await refresh_tokens_collection.find({
            "isRevoked": False,
            "expiresAt": {"$gt": datetime.utcnow()}
        }).to_list(length=None)
        
        # Group by user
        user_sessions = {}
        for session in sessions:
            user_id = str(session["userId"])
            if user_id not in user_sessions:
                user_sessions[user_id] = []
            
            user_sessions[user_id].append({
                "id": str(session["_id"]),
                "device_info": session.get("deviceInfo"),
                "ip_address": session.get("ipAddress"),
                "created_at": session["createdAt"],
                "expires_at": session["expiresAt"]
            })
        
        return {
            "success": True,
            "sessions_by_user": user_sessions,
            "total_users": len(user_sessions),
            "total_sessions": len(sessions)
        }
        
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Lỗi khi lấy thông tin phiên!"
            }
        )

# Revoke user sessions (admin only)
@router.post("/admin/sessions/{user_id}/revoke", dependencies=[Depends(require_permission_dep(Permission.MANAGE_ALL_SESSIONS)), Depends(strict_rate_limit)])
async def admin_revoke_user_sessions(user_id: str, current_user: dict = Depends(get_current_user)):
    """Revoke all sessions for a specific user (admin only)"""
    from ...shared.session_manager import session_manager
    
    success = await session_manager.revoke_all_user_tokens(user_id)
    
    if success:
        return {
            "success": True,
            "message": f"Đã thu hồi tất cả phiên của user {user_id}!"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Lỗi khi thu hồi phiên!"
            }
        )

# OAuth endpoints (placeholder for future implementation)
@router.get("/oauth/google")
async def google_oauth():
    """Google OAuth placeholder"""
    return {
        "message": "Google OAuth endpoint - implement with OAuth library",
        "status": "not_implemented"
    }

@router.get("/oauth/facebook")
async def facebook_oauth():
    """Facebook OAuth placeholder"""
    return {
        "message": "Facebook OAuth endpoint - implement with OAuth library", 
        "status": "not_implemented"
    }

# System status endpoints

# Auth system status
@router.get("/status")
async def auth_status():
    """Authentication system status"""
    return {
        "success": True,
        "system": "Voux Authentication Service",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "authentication": {
            "primary": "jwt-with-refresh-tokens",
            "session_management": True,
            "rbac_enabled": True,
            "token_blacklisting": True
        },
        "available_features": {
            "registration": True,
            "login": True,
            "logout": True,
            "token_refresh": True,
            "password_change": True,
            "session_management": True,
            "rbac": True,
            "rate_limiting": True,
            "audit_logging": True,
            "oauth_google": False,
            "oauth_facebook": False
        },
        "security_features": {
            "bcrypt_hashing": True,
            "jwt_tokens": True,
            "refresh_tokens": True,
            "token_blacklisting": True,
            "session_tracking": True,
            "role_based_access": True,
            "permission_system": True
        }
    }

# RBAC information endpoint
@router.get("/rbac/info", dependencies=[Depends(get_current_user)])
async def rbac_info(current_user: dict = Depends(get_current_user)):
    """Get RBAC information for current user"""
    from ...shared.rbac import RBACManager, Role, Permission
    
    user_role = RBACManager.get_user_role(current_user)
    user_permissions = list(RBACManager.get_user_permissions(current_user))
    
    return {
        "success": True,
        "user": {
            "id": current_user.get("id"),
            "username": current_user.get("username"),
            "role": user_role.value,
            "permissions": user_permissions
        },
        "available_roles": [role.value for role in Role],
        "available_permissions": [perm.value for perm in Permission]
    } 