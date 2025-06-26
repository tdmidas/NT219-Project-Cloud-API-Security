# RBAC Helper Functions
# Add these to your controllers for consistent RBAC usage

from shared.rbac import RBACManager, Permission
from fastapi import HTTPException, status

def require_permission(current_user: dict, permission: Permission):
    """Helper function to check if user has required permission"""
    if not RBACManager.has_permission(current_user, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Bạn không có quyền thực hiện hành động này!",
                "error_code": "INSUFFICIENT_PERMISSIONS"
            }
        )

def require_admin_access(current_user: dict):
    """Helper function to require admin access"""
    require_permission(current_user, Permission.ADMIN_ACCESS)

def require_owner_or_admin(current_user: dict, resource_owner_id: str):
    """Helper function to check if user is owner or admin"""
    user_id = current_user.get("id")
    is_owner = str(user_id) == str(resource_owner_id)
    is_admin = RBACManager.has_permission(current_user, Permission.ADMIN_ACCESS)
    
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Bạn chỉ có thể truy cập tài nguyên của chính mình!",
                "error_code": "ACCESS_DENIED"
            }
        )

def get_user_role_string(current_user: dict) -> str:
    """Get user role as string for display purposes"""
    role = RBACManager.get_user_role(current_user)
    return role.value

def check_role_hierarchy(current_user: dict, target_role: str) -> bool:
    """Check if current user can manage users with target role"""
    current_role = RBACManager.get_user_role(current_user)
    
    # Role hierarchy: SUPER_ADMIN > ADMIN > MODERATOR > VOUCHER_CREATOR > USER > GUEST
    role_levels = {
        "GUEST": 0,
        "USER": 1,
        "VOUCHER_CREATOR": 2,
        "MODERATOR": 3,
        "ADMIN": 4,
        "SUPER_ADMIN": 5
    }
    
    current_level = role_levels.get(current_role.value, 0)
    target_level = role_levels.get(target_role, 0)
    
    return current_level > target_level
