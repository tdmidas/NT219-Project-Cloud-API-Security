from enum import Enum
from typing import Dict, List, Set, Optional, Callable
from fastapi import HTTPException, status, Depends
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class Permission(str, Enum):
    """System permissions"""
    # User permissions
    READ_USERS = "read:users"
    CREATE_USERS = "create:users" 
    UPDATE_USERS = "update:users"
    DELETE_USERS = "delete:users"
    UPDATE_OWN_PROFILE = "update:own_profile"
    
    # Voucher permissions
    READ_VOUCHERS = "read:vouchers"
    CREATE_VOUCHERS = "create:vouchers"
    UPDATE_VOUCHERS = "update:vouchers"
    DELETE_VOUCHERS = "delete:vouchers"
    UPDATE_OWN_VOUCHERS = "update:own_vouchers"
    DELETE_OWN_VOUCHERS = "delete:own_vouchers"
    
    # Cart permissions
    READ_OWN_CART = "read:own_cart"
    MANAGE_OWN_CART = "manage:own_cart"
    
    # Admin permissions
    ADMIN_ACCESS = "admin:access"
    MANAGE_SYSTEM = "manage:system"
    VIEW_ANALYTICS = "view:analytics"
    
    # Session management
    MANAGE_OWN_SESSIONS = "manage:own_sessions"
    MANAGE_ALL_SESSIONS = "manage:all_sessions"

class Role(str, Enum):
    """User roles"""
    GUEST = "guest"
    USER = "user"
    VOUCHER_CREATOR = "voucher_creator"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "SUPER_ADMIN"

# Role-Permission mapping
ROLE_PERMISSIONS = {
    Role.GUEST: {
        Permission.READ_VOUCHERS,
    },
    Role.USER: {
        # Basic voucher permissions
        Permission.READ_VOUCHERS,
        
        # Cart permissions - THÊM VÀO ĐÂY
        Permission.READ_OWN_CART,
        Permission.MANAGE_OWN_CART,
        
        # Profile permissions
        Permission.UPDATE_OWN_PROFILE,
        
        # Session permissions
        Permission.MANAGE_OWN_SESSIONS,
    },
    Role.VOUCHER_CREATOR: {
        # Inherit user permissions
        Permission.READ_VOUCHERS,
        Permission.READ_OWN_CART,
        Permission.MANAGE_OWN_CART,
        Permission.UPDATE_OWN_PROFILE,
        Permission.MANAGE_OWN_SESSIONS,
        
        # Voucher creation permissions
        Permission.CREATE_VOUCHERS,
        Permission.UPDATE_OWN_VOUCHERS,
        Permission.DELETE_OWN_VOUCHERS,
    },
    Role.MODERATOR: {
        # Inherit voucher creator permissions
        Permission.READ_VOUCHERS,
        Permission.CREATE_VOUCHERS,
        Permission.UPDATE_OWN_VOUCHERS,
        Permission.DELETE_OWN_VOUCHERS,
        Permission.READ_OWN_CART,
        Permission.MANAGE_OWN_CART,
        Permission.UPDATE_OWN_PROFILE,
        Permission.MANAGE_OWN_SESSIONS,
        
        # Moderation permissions
        Permission.UPDATE_VOUCHERS,
        Permission.DELETE_VOUCHERS,
        Permission.VIEW_ANALYTICS,
    },
    Role.ADMIN: {
        # All permissions except super admin ones
        Permission.READ_USERS,
        Permission.CREATE_USERS,
        Permission.UPDATE_USERS,
        Permission.DELETE_USERS,
        Permission.UPDATE_OWN_PROFILE,
        
        Permission.READ_VOUCHERS,
        Permission.CREATE_VOUCHERS,
        Permission.UPDATE_VOUCHERS,
        Permission.DELETE_VOUCHERS,
        Permission.UPDATE_OWN_VOUCHERS,
        Permission.DELETE_OWN_VOUCHERS,
        
        Permission.READ_OWN_CART,
        Permission.MANAGE_OWN_CART,
        
        Permission.ADMIN_ACCESS,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_OWN_SESSIONS,
        Permission.MANAGE_ALL_SESSIONS,
    },
    Role.SUPER_ADMIN: {
        # All permissions
        *[perm for perm in Permission]
    }
}

class RBACManager:
    """Role-Based Access Control Manager"""
    
    @staticmethod
    def get_user_role(user: Dict) -> Role:
        """Determine user role based on rbac_role field only"""
        rbac_role = user.get("rbac_role", "USER")
        try:
            return Role(rbac_role)
        except ValueError:
            # Default to USER if invalid role
            return Role.USER
    
    @staticmethod
    def get_user_permissions(user: Dict) -> Set[Permission]:
        """Get all permissions for a user"""
        role = RBACManager.get_user_role(user)
        return ROLE_PERMISSIONS.get(role, set())
    
    @staticmethod
    def has_permission(user: Dict, permission: Permission) -> bool:
        """Check if user has specific permission"""
        user_permissions = RBACManager.get_user_permissions(user)
        return permission in user_permissions
    
    @staticmethod
    def has_any_permission(user: Dict, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        user_permissions = RBACManager.get_user_permissions(user)
        return any(perm in user_permissions for perm in permissions)
    
    @staticmethod
    def can_access_resource(user: Dict, resource_owner_id: Optional[str], required_permission: Permission, ownership_permission: Optional[Permission] = None) -> bool:
        """Check if user can access a resource (considering ownership)"""
        user_permissions = RBACManager.get_user_permissions(user)
        
        # Check if user has general permission
        if required_permission in user_permissions:
            return True
        
        # Check ownership-based permission
        if ownership_permission and ownership_permission in user_permissions:
            return user.get("id") == resource_owner_id
        
        return False

# Permission decorators
def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get("current_user")
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
                        "required_permission": permission.value
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_any_permission(permissions: List[Permission]):
    """Decorator to require any of the specified permissions"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Authentication required"
                    }
                )
            
            if not RBACManager.has_any_permission(current_user, permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "message": "Insufficient permissions",
                        "required_permissions": [p.value for p in permissions]
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def require_ownership_or_permission(required_permission: Permission, ownership_permission: Permission):
    """Decorator to require ownership or specific permission"""
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": "Authentication required"
                    }
                )
            
            # Extract resource owner ID from kwargs or args
            resource_owner_id = kwargs.get("user_id") or kwargs.get("resource_owner_id")
            
            if not RBACManager.can_access_resource(
                current_user, 
                resource_owner_id, 
                required_permission, 
                ownership_permission
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "message": "Access denied - insufficient permissions or not resource owner"
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# FastAPI dependency functions
def require_admin():
    """FastAPI dependency to require admin role"""
    def check_admin(current_user: Dict = Depends(lambda: None)):
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"success": False, "message": "Authentication required"}
            )
        
        if not RBACManager.has_permission(current_user, Permission.ADMIN_ACCESS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"success": False, "message": "Admin access required"}
            )
        
        return current_user
    
    return check_admin

def require_role(required_role: Role):
    """FastAPI dependency to require specific role"""
    def check_role(current_user: Dict = Depends(lambda: None)):
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"success": False, "message": "Authentication required"}
            )
        
        user_role = RBACManager.get_user_role(current_user)
        if user_role != required_role and user_role not in [Role.ADMIN, Role.SUPER_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False, 
                    "message": f"Role '{required_role.value}' required",
                    "user_role": user_role.value
                }
            )
        
        return current_user
    
    return check_role