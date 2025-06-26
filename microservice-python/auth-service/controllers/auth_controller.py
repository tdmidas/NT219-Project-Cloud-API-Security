import bcrypt
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status, Request
from pydantic import BaseModel, EmailStr
import time
from datetime import datetime, timedelta
from bson import ObjectId
import jwt
import os
import asyncio

# Flexible imports
try:
    # Try relative imports first (when running as module)
    from ...shared.models.user import User, UserCreate, UserResponse
    from ...shared.database import AuthDatabase
    from ...shared.middleware import AuthMiddleware
    from ...shared.session_manager import session_manager
    from ...shared.rbac import RBACManager, Permission
    from ...shared.event_manager import event_manager
except ImportError:
    # Fallback to absolute imports (when running directly)
    from shared.models.user import User, UserCreate, UserResponse
    from shared.database import AuthDatabase
    from shared.middleware import AuthMiddleware
    from shared.session_manager import session_manager
    from shared.rbac import RBACManager, Permission
    from shared.event_manager import event_manager

logger = logging.getLogger(__name__)

# Pydantic models for requests
class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None
    logout_all: bool = False

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class AuthController:
    """JWT-based authentication controller with session management"""
    
    def __init__(self):
        self.auth_middleware = AuthMiddleware()
        self.jwt_secret = os.getenv("JWT_ACCESS_KEY", "your-secret-key")
    
    async def register(self, user_data: UserCreate) -> Dict[str, Any]:
        """User registration with validation"""
        try:
            # Basic validation is handled by Pydantic
            
            # Password strength validation
            if len(user_data.password) < 8:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Mật khẩu phải có ít nhất 8 ký tự!"
                    }
                )
            
            # Check if user already exists
            users_collection = AuthDatabase.get_collection("users")
            
            existing_user = await users_collection.find_one({
                "$or": [
                    {"username": user_data.username},
                    {"email": user_data.email}
                ]
            })
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Username hoặc email đã tồn tại!"
                    }
                )
            
            # Hash password with salt
            salt = bcrypt.gensalt(rounds=12)
            hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), salt)
            
            # Create new user with default role
            user_dict = {
                "username": user_data.username,
                "email": user_data.email,
                "password": hashed_password.decode('utf-8'),
                "admin": False,
                "roles": ["user"],  # Default role
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": None,
                "login_count": 0
            }
            
            result = await users_collection.insert_one(user_dict)
            
            if result.inserted_id:
                # Prepare user event data
                user_event_data = {
                    "user_id": str(result.inserted_id),
                    "username": user_data.username,
                    "email": user_data.email,
                    "admin": False,
                    "roles": ["user"],
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                # Async publish event (non-blocking - fire and forget)
                try:
                    asyncio.create_task(
                        event_manager.publish_event("user.registered", user_event_data)
                    )
                    logger.info(f"Event publishing scheduled for user: {user_data.username}")
                except Exception as e:
                    logger.warning(f"Could not schedule event publishing: {e}")
                    # Continue - not critical for registration success
                
                return {
                    "success": True,
                    "message": "Đăng ký tài khoản thành công! 🎉"
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "success": False,
                        "message": "Lỗi khi tạo tài khoản!"
                    }
                )
                
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Registration error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi server! Vui lòng thử lại sau."
                }
            )
    
    async def login(self, login_data: LoginRequest, request: Request) -> Dict[str, Any]:
        """Enhanced JWT-based login with refresh tokens"""
        try:
            logger.info(f"Login attempt for user: {login_data.username}")
            
            # Authenticate user
            users_collection = AuthDatabase.get_collection("users")
            user = await users_collection.find_one({"username": login_data.username})
            
            if not user:
                logger.warning(f"Login failed - user not found: {login_data.username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Tên đăng nhập không đúng!"
                    }
                )
            
            # Verify password
            if not bcrypt.checkpw(login_data.password.encode('utf-8'), user["password"].encode('utf-8')):
                logger.warning(f"Login failed - wrong password for user: {login_data.username}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Mật khẩu không đúng!"
                    }
                )
            
            # Update login statistics
            try:
                await users_collection.update_one(
                    {"_id": user["_id"]},
                    {
                        "$set": {"last_login": datetime.utcnow()},
                        "$inc": {"login_count": 1}
                    }
                )
                logger.info(f"Updated login stats for user: {login_data.username}")
            except Exception as e:
                logger.warning(f"Could not update login stats: {e}")
                # Continue - not critical
            
            # Generate tokens
            user_id = str(user["_id"])
            token_data = {
                "user_id": user_id,
                "username": user["username"],
                "rbac_role": user.get("rbac_role", "USER")
            }
            
            # Generate access token (45 seconds: 30s session + 15s grace period for user decision)
            try:
                access_token = self.auth_middleware.generate_jwt_token(
                    token_data, 
                    expires_delta=timedelta(seconds=45)
                )
                logger.info(f"Generated access token for user: {login_data.username}")
            except Exception as e:
                logger.error(f"Failed to generate access token: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "success": False,
                        "message": "Lỗi tạo token truy cập!"
                    }
                )
            
            # Generate refresh token (30 days or 7 days)
            try:
                expiry_days = 30 if login_data.remember_me else 7
                logger.info(f"Creating refresh token for user: {login_data.username}")
                refresh_token = await session_manager.create_refresh_token(
                    user_id,
                    device_info=request.headers.get("user-agent"),
                    ip_address=request.client.host if hasattr(request, 'client') and request.client else None
                )
                logger.info(f"Successfully created refresh token for user: {login_data.username}")
            except Exception as e:
                logger.error(f"Failed to create refresh token for user {login_data.username}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "success": False,
                        "message": "Lỗi tạo refresh token!",
                        "error": str(e)
                    }
                )
            
            # Prepare secure user response (only essential information)
            secure_user_info = {
                "id": user_id,
                "username": user["username"],
                "rbac_role": user.get("rbac_role", "USER"),
                "avatar_url": user.get("avatar_url", "/default-avatar.png"),
                "theme": user.get("theme", "light")
            }
            
            # Add RBAC information
            try:
                rbac_role = RBACManager.get_user_role(token_data)
                permissions = list(RBACManager.get_user_permissions(token_data))
            except Exception as e:
                logger.warning(f"RBAC error for user {login_data.username}: {e}")
                rbac_role = None
                permissions = []
            
            logger.info(f"Login successful for user: {login_data.username}")
            
            return {
                "success": True,
                "message": "Đăng nhập thành công! 🎉 (Phiên làm việc: 30 giây)",
                "user": secure_user_info,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": 30,  # Client sees 30 seconds, but token valid for 45s
                "actual_token_expiry": 45,  # Actual backend expiry
                "refresh_expires_in": 600,  # 10 minutes (600 seconds)
                "auth_type": "jwt_with_refresh",
                "session_warning": "⚠️ Bạn sẽ được hỏi có muốn tiếp tục sau 30 giây!",
                "rbac": {
                    "role": rbac_role.value if rbac_role else "user",
                    "permissions": permissions
                }
            }
            
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Login error for user {login_data.username}: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi server khi đăng nhập!",
                    "error": str(error)
                }
            )
    
    async def logout(self, request: Request, logout_data: Optional[LogoutRequest] = None, current_user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Enhanced logout with token revocation"""
        try:
            user_id = current_user.get("id") if current_user else "unknown"
            logger.info(f"Logout attempt for user: {user_id}")
            
            # Get access token from request
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                access_token = auth_header.split(" ")[1]
                session_manager.blacklist_access_token(access_token)
                logger.info(f"Blacklisted access token for user: {user_id}")
            
            logout_all = False
            
            if logout_data and logout_data.refresh_token:
                # Revoke specific refresh token
                logger.info(f"Revoking specific refresh token for user: {user_id}")
                try:
                    await session_manager.revoke_refresh_token(logout_data.refresh_token)
                except Exception as e:
                    logger.warning(f"Could not revoke specific refresh token: {e}")
                    
            elif logout_data and logout_data.logout_all and current_user:
                # Revoke all user sessions
                logger.info(f"Revoking all sessions for user: {user_id}")
                logout_all = True
                try:
                    await session_manager.revoke_all_user_tokens(current_user.get("id"))
                except Exception as e:
                    logger.warning(f"Could not revoke all user tokens: {e}")
                    
            elif current_user:
                # Revoke all sessions for current user (default behavior)
                logger.info(f"Revoking all sessions for current user: {user_id}")
                logout_all = True
                try:
                    await session_manager.revoke_all_user_tokens(current_user.get("id"))
                except Exception as e:
                    logger.warning(f"Could not revoke all user tokens: {e}")
            
            logger.info(f"Logout successful for user: {user_id} (logout_all: {logout_all})")
            
            return {
                "success": True,
                "message": "Đăng xuất thành công! 👋"
            }
                
        except Exception as error:
            logger.error(f"Logout error for user {current_user.get('id') if current_user else 'unknown'}: {error}")
            # Return success anyway - logout should always appear to work from user perspective
            return {
                "success": True,
                "message": "Đăng xuất thành công! 👋"
            }
    
    async def refresh_token(self, refresh_request: RefreshTokenRequest, request: Request) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            # Validate refresh token
            user_data = await session_manager.validate_refresh_token(refresh_request.refresh_token)
            
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Refresh token không hợp lệ hoặc đã hết hạn!"
                    }
                )
            
            # Generate new access token
            token_data = {
                "user_id": user_data.get("user_id"),
                "username": user_data.get("username"),
                "rbac_role": user_data.get("rbac_role", "USER")
            }
            
            new_access_token = self.auth_middleware.generate_jwt_token(
                token_data,
                expires_delta=timedelta(seconds=45)
            )
            
            # Optionally rotate refresh token (security best practice)
            new_refresh_token = await session_manager.create_refresh_token(
                user_data.get("user_id"),
                device_info=request.headers.get("user-agent"),
                ip_address=request.client.host
            )
            
            # Revoke old refresh token
            await session_manager.revoke_refresh_token(refresh_request.refresh_token)
            
            return {
                "success": True,
                "message": "Token đã được refresh! (Phiên mới: 30 giây)",
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "Bearer",
                "expires_in": 30,  # Client sees 30 seconds, but token valid for 45s
                "actual_token_expiry": 45,  # Actual backend expiry
                "refresh_expires_in": 600,  # 10 minutes (600 seconds)
                "session_warning": "⚠️ Bạn sẽ được hỏi có muốn tiếp tục sau 30 giây!"
            }
            
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Token refresh error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi refresh token!",
                    "error": str(error)
                }
            )

    async def get_profile(self, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Get user profile with RBAC information"""
        try:
            users_collection = AuthDatabase.get_collection("users")
            user = await users_collection.find_one({"_id": ObjectId(current_user.get("id"))})
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": "Không tìm thấy người dùng!"
                    }
                )
            
            # Prepare secure profile response (exclude sensitive information)
            secure_profile = {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],  # Email is okay in profile context
                "rbac_role": user.get("rbac_role", "USER"),
                "avatar_url": user.get("avatar_url", "/default-avatar.png"),
                "bio": user.get("bio"),
                "theme": user.get("theme", "light"),
                "vouchers_posted": user.get("vouchers_posted", 0),
                "vouchers_sold": user.get("vouchers_sold", 0),
                "vouchers_bought": user.get("vouchers_bought", 0),
                "wallet": {
                    "balance": user.get("wallet", {}).get("balance", 0.0)
                    # Exclude wallet history for security - use separate endpoint
                },
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login")
            }
            
            # Add RBAC information
            rbac_role = RBACManager.get_user_role(current_user)
            permissions = list(RBACManager.get_user_permissions(current_user))
            
            return {
                "success": True,
                "user": secure_profile,
                "rbac": {
                    "role": rbac_role.value,
                    "permissions": permissions
                }
            }
            
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Get profile error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi lấy thông tin profile!",
                    "error": str(error)
                }
            )
    
    async def change_password(self, password_request: ChangePasswordRequest, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Change user password"""
        try:
            users_collection = AuthDatabase.get_collection("users")
            user = await users_collection.find_one({"_id": ObjectId(current_user.get("id"))})
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": "Không tìm thấy người dùng!"
                    }
                )
            
            # Verify current password
            if not bcrypt.checkpw(password_request.current_password.encode('utf-8'), user["password"].encode('utf-8')):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Mật khẩu hiện tại không đúng!"
                    }
                )
            
            # Validate new password
            if len(password_request.new_password) < 8:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Mật khẩu mới phải có ít nhất 8 ký tự!"
                    }
                )
            
            # Hash new password
            salt = bcrypt.gensalt(rounds=12)
            hashed_password = bcrypt.hashpw(password_request.new_password.encode('utf-8'), salt)
            
            # Update password
            await users_collection.update_one(
                {"_id": ObjectId(current_user.get("id"))},
                {
                    "$set": {
                        "password": hashed_password.decode('utf-8'),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Revoke all existing sessions (force re-login)
            await session_manager.revoke_all_user_tokens(current_user.get("id"))
            
            return {
                "success": True,
                "message": "Đổi mật khẩu thành công! Vui lòng đăng nhập lại."
            }
            
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Change password error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi đổi mật khẩu!",
                    "error": str(error)
                }
            )
    
    async def get_user_sessions(self, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Get user's active sessions"""
        try:
            sessions = await session_manager.get_user_sessions(current_user.get("id"))
            
            return {
                "success": True,
                "sessions": sessions,
                "total": len(sessions)
            }
            
        except Exception as error:
            logger.error(f"Get sessions error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi lấy danh sách phiên!"
                }
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            # Check if token is blacklisted
            if session_manager.is_access_token_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Token đã bị thu hồi!"
                    }
                )
            
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return {
                "success": True,
                "payload": payload,
                "valid": True
            }
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Token đã hết hạn!",
                    "error_code": "TOKEN_EXPIRED"
                }
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Token không hợp lệ!",
                    "error_code": "INVALID_TOKEN"
                }
            )

# Create controller instance
auth_controller = AuthController()