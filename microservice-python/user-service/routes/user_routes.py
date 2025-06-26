from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

# Flexible imports
try:
    # Try relative imports first (when running as module)
    from ..controllers.user_controller import (
        user_controller, 
        UserProfileUpdate, 
        WalletTransaction
    )
    from ...shared.middleware import (
        get_current_user, 
        require_permission_dep,
        normal_rate_limit,
        strict_rate_limit
    )
    from ...shared.rbac import Permission, RBACManager
    from ...shared.database import UserDatabase
except ImportError:
    try:
        # Try absolute imports from microservice-python directory
        from user_service.controllers.user_controller import (
            user_controller, 
            UserProfileUpdate, 
            WalletTransaction
        )
        from shared.middleware import (
            get_current_user, 
            require_permission_dep,
            normal_rate_limit,
            strict_rate_limit
        )
        from shared.rbac import Permission, RBACManager
        from shared.database import UserDatabase
    except ImportError:
        # Final fallback - add parent paths
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(os.path.dirname(current_dir))
        sys.path.append(parent_dir)
        
        from controllers.user_controller import (
            user_controller, 
            UserProfileUpdate, 
            WalletTransaction
        )
        from shared.middleware import (
            get_current_user, 
            require_permission_dep,
            normal_rate_limit,
            strict_rate_limit
        )
        from shared.rbac import Permission, RBACManager
        from shared.database import UserDatabase

router = APIRouter()

# Get all users (admin only)
@router.get("/", dependencies=[Depends(require_permission_dep(Permission.READ_USERS)), Depends(normal_rate_limit)])
async def get_all_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    current_user: dict = Depends(require_permission_dep(Permission.READ_USERS))
):
    """Get all users with pagination (requires READ_USERS permission)"""
    return await user_controller.get_all_users(skip, limit)

# Get user profile by ID (anyone can view profiles, but sensitive data filtered)
@router.get("/{user_id}", dependencies=[Depends(get_current_user), Depends(normal_rate_limit)])
async def get_user_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user profile by ID (public profile data)"""
    return await user_controller.get_user_profile(user_id)

# Get current user's profile (own profile access)
@router.get("/profile/me", dependencies=[Depends(require_permission_dep(Permission.UPDATE_OWN_PROFILE)), Depends(normal_rate_limit)])
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile (requires UPDATE_OWN_PROFILE permission)"""
    return await user_controller.get_my_profile(current_user)

# Update user profile (admin or owner)
@router.put("/{user_id}", dependencies=[Depends(get_current_user), Depends(normal_rate_limit)])
async def update_user_profile(
    user_id: str,
    update_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile (requires UPDATE_USERS permission or ownership + UPDATE_OWN_PROFILE)"""
    # Check permissions: admin can update any profile, users can only update their own
    can_update_any = RBACManager.has_permission(current_user, Permission.UPDATE_USERS)
    can_update_own = (RBACManager.has_permission(current_user, Permission.UPDATE_OWN_PROFILE) 
                     and current_user.get("id") == user_id)
    
    if not (can_update_any or can_update_own):
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "message": "Insufficient permissions to update this profile",
                "required": "UPDATE_USERS permission or ownership + UPDATE_OWN_PROFILE"
            }
        )
    
    return await user_controller.update_user_profile(user_id, update_data, current_user)

# Update current user's profile
@router.put("/profile/me", dependencies=[Depends(require_permission_dep(Permission.UPDATE_OWN_PROFILE)), Depends(normal_rate_limit)])
async def update_my_profile(
    update_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile (requires UPDATE_OWN_PROFILE permission)"""
    user_id = current_user.get("id")
    return await user_controller.update_user_profile(user_id, update_data, current_user)

# Delete user (admin only)
@router.delete("/{user_id}", dependencies=[Depends(require_permission_dep(Permission.DELETE_USERS)), Depends(strict_rate_limit)])
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_permission_dep(Permission.DELETE_USERS))
):
    """Delete user (requires DELETE_USERS permission - admin only)"""
    return await user_controller.delete_user(user_id, current_user)

# Wallet management endpoints

# Get wallet balance (owner or admin with READ_USERS)
@router.get("/{user_id}/wallet", dependencies=[Depends(get_current_user), Depends(normal_rate_limit)])
async def get_wallet_balance(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user wallet balance (owner or admin)"""
    # Check permission: admin can view any wallet, users can only view their own
    can_read_any = RBACManager.has_permission(current_user, Permission.READ_USERS)
    is_owner = current_user.get("id") == user_id
    
    if not (can_read_any or is_owner):
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "message": "Bạn không có quyền xem ví này!",
                "required": "READ_USERS permission or ownership"
            }
        )
    
    user_data = await user_controller.get_user_profile(user_id)
    wallet = user_data.get("user", {}).get("wallet", {"balance": 0.0, "history": []})
    
    return {
        "success": True,
        "wallet": wallet
    }

# Wallet transaction (owner only for now)
@router.post("/{user_id}/wallet/transaction", dependencies=[Depends(get_current_user), Depends(strict_rate_limit)])
async def wallet_transaction(
    user_id: str,
    transaction: WalletTransaction,
    current_user: dict = Depends(get_current_user)
):
    """Manage user wallet transactions (owner only for security)"""
    # Only the owner can manage their wallet (for security reasons)
    if current_user.get("id") != user_id:
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "message": "Bạn chỉ có thể thao tác với ví của chính mình!"
            }
        )
    
    return await user_controller.manage_wallet(user_id, transaction, current_user)

# Admin-only endpoints

# User statistics (admin only)
@router.get("/stats/overview", dependencies=[Depends(require_permission_dep(Permission.VIEW_ANALYTICS)), Depends(normal_rate_limit)])
async def user_statistics(current_user: dict = Depends(require_permission_dep(Permission.VIEW_ANALYTICS))):
    """Get user statistics overview (requires VIEW_ANALYTICS permission)"""
    from datetime import datetime, timedelta
    
    try:
        users_collection = UserDatabase.get_collection("users")
        
        # Basic statistics
        total_users = await users_collection.count_documents({})
        admin_users = await users_collection.count_documents({"rbac_role": {"$in": ["ADMIN", "SUPER_ADMIN"]}})
        regular_users = total_users - admin_users
        
        # Users created in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = await users_collection.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        
        # Active users (logged in last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_users = await users_collection.count_documents({
            "last_login": {"$gte": seven_days_ago}
        })
        
        return {
            "success": True,
            "statistics": {
                "total_users": total_users,
                "recent_users": recent_users,
                "active_users": active_users,
                "admin_users": admin_users,
                "regular_users": regular_users,
                "period": "last_30_days"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": "Error fetching user statistics",
            "error": str(e)
        }

# Create user (admin only)
@router.post("/", dependencies=[Depends(require_permission_dep(Permission.CREATE_USERS)), Depends(strict_rate_limit)])
async def create_user_admin(
    user_data: dict,
    current_user: dict = Depends(require_permission_dep(Permission.CREATE_USERS))
):
    """Create user (admin only - requires CREATE_USERS permission)"""
    # This endpoint allows admins to create users with specific roles
    return {
        "success": False,
        "message": "Admin user creation endpoint - not implemented yet",
        "note": "Use registration endpoint for regular user creation"
    }

# Update user role (admin only)
@router.post("/{user_id}/role", dependencies=[Depends(require_permission_dep(Permission.UPDATE_USERS)), Depends(strict_rate_limit)])
async def update_user_role(
    user_id: str,
    role_data: dict,
    current_user: dict = Depends(require_permission_dep(Permission.UPDATE_USERS))
):
    """Update user role (admin only - requires UPDATE_USERS permission)"""
    # Implementation for changing user roles
    return {
        "success": False,
        "message": "User role update endpoint - not implemented yet",
        "user_id": user_id,
        "requested_role": role_data
    }