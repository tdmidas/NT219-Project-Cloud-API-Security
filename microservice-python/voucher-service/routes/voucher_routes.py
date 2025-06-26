from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

# Flexible imports
try:
    # Try relative imports first (when running as module)
    from ..controllers.voucher_controller import (
        voucher_controller, 
        VoucherCreate, 
        VoucherUpdate
    )
    from ...shared.middleware import (
        get_current_user, 
        get_current_user_optional,
        require_permission_dep,
        normal_rate_limit,
        strict_rate_limit,
        public_rate_limit
    )
    from ...shared.rbac import Permission, RBACManager
except ImportError:
    try:
        # Try absolute imports from microservice-python directory
        from voucher_service.controllers.voucher_controller import (
            voucher_controller, 
            VoucherCreate, 
            VoucherUpdate
        )
        from shared.middleware import (
            get_current_user, 
            get_current_user_optional,
            require_permission_dep,
            normal_rate_limit,
            strict_rate_limit,
            public_rate_limit
        )
        from shared.rbac import Permission, RBACManager
    except ImportError:
        # Final fallback - add parent paths
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(os.path.dirname(current_dir))
        sys.path.append(parent_dir)
        
        from controllers.voucher_controller import (
            voucher_controller, 
            VoucherCreate, 
            VoucherUpdate
        )
        from shared.middleware import (
            get_current_user, 
            get_current_user_optional,
            require_permission_dep,
            normal_rate_limit,
            strict_rate_limit,
            public_rate_limit
        )
        from shared.rbac import Permission, RBACManager

router = APIRouter()

# Public endpoints (no authentication required)

# Get all vouchers (public endpoint with pagination)
@router.get("/getAllVoucher", dependencies=[Depends(public_rate_limit)])
async def get_all_vouchers(
    skip: int = Query(0, ge=0, description="Number of vouchers to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of vouchers to return"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Get all vouchers with pagination and filtering (public access)"""
    return await voucher_controller.get_all_vouchers(skip, limit, category)

# Get valid vouchers (for public access)
@router.get("/getValidVouchers", dependencies=[Depends(public_rate_limit)])
async def get_valid_vouchers():
    """Get valid vouchers (not expired, quantity > 0) - public access"""
    vouchers = await voucher_controller.get_valid_vouchers()
    return vouchers

# Get voucher by ID (public)
@router.get("/{voucher_id}", dependencies=[Depends(public_rate_limit)])
async def get_voucher_by_id(voucher_id: str):
    """Get voucher by ID (public access)"""
    return await voucher_controller.get_voucher_by_id(voucher_id)

# Search vouchers (public)
@router.get("/search/", dependencies=[Depends(public_rate_limit)])
async def search_vouchers(
    q: str = Query(..., min_length=1, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results")
):
    """Search vouchers by title, description, or category (public access)"""
    return await voucher_controller.search_vouchers(q, category, limit)

# Get categories (public)
@router.get("/categories/", dependencies=[Depends(public_rate_limit)])
async def get_categories():
    """Get all voucher categories (public access)"""
    return await voucher_controller.get_categories()

# Get vouchers by category (public)
@router.get("/category/{category}", dependencies=[Depends(public_rate_limit)])
async def get_vouchers_by_category(
    category: str,
    skip: int = Query(0, ge=0, description="Number of vouchers to skip"),
    limit: int = Query(50, ge=1, le=200, description="Number of vouchers to return")
):
    """Get vouchers by specific category (public access)"""
    return await voucher_controller.get_all_vouchers(skip, limit, category)

# Protected endpoints (require authentication and permissions)

# Create voucher (requires CREATE_VOUCHERS permission)
@router.post("/createVoucher", dependencies=[Depends(require_permission_dep(Permission.CREATE_VOUCHERS)), Depends(normal_rate_limit)])
async def create_voucher(
    voucher_data: VoucherCreate,
    current_user: dict = Depends(require_permission_dep(Permission.CREATE_VOUCHERS))
):
    """Create new voucher (requires CREATE_VOUCHERS permission)"""
    return await voucher_controller.create_voucher(voucher_data, current_user)

# Update voucher (owner with UPDATE_OWN_VOUCHERS or admin with UPDATE_VOUCHERS)
@router.put("/updateVoucher/{voucher_id}", dependencies=[Depends(get_current_user), Depends(normal_rate_limit)])
async def update_voucher(
    voucher_id: str,
    update_data: VoucherUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update voucher (owner with UPDATE_OWN_VOUCHERS or admin with UPDATE_VOUCHERS)"""
    # Get voucher to check ownership
    voucher_data = await voucher_controller.get_voucher_by_id(voucher_id)
    if not voucher_data.get("success"):
        raise HTTPException(status_code=404, detail=voucher_data)
    
    voucher = voucher_data.get("voucher", {})
    voucher_owner_id = voucher.get("created_by")
    
    # Check permissions: admin can update any voucher, users can only update their own
    can_update_any = RBACManager.has_permission(current_user, Permission.UPDATE_VOUCHERS)
    can_update_own = (RBACManager.has_permission(current_user, Permission.UPDATE_OWN_VOUCHERS) 
                     and current_user.get("id") == voucher_owner_id)
    
    if not (can_update_any or can_update_own):
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "message": "Insufficient permissions to update this voucher",
                "required": "UPDATE_VOUCHERS permission or ownership + UPDATE_OWN_VOUCHERS"
            }
        )
    
    return await voucher_controller.update_voucher(voucher_id, update_data, current_user)

# Delete voucher (owner with DELETE_OWN_VOUCHERS or admin with DELETE_VOUCHERS)
@router.delete("/deleteVoucher/{voucher_id}", dependencies=[Depends(get_current_user), Depends(strict_rate_limit)])
async def delete_voucher(
    voucher_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete voucher (owner with DELETE_OWN_VOUCHERS or admin with DELETE_VOUCHERS)"""
    # Get voucher to check ownership
    voucher_data = await voucher_controller.get_voucher_by_id(voucher_id)
    if not voucher_data.get("success"):
        raise HTTPException(status_code=404, detail=voucher_data)
    
    voucher = voucher_data.get("voucher", {})
    voucher_owner_id = voucher.get("created_by")
    
    # Check permissions: admin can delete any voucher, users can only delete their own
    can_delete_any = RBACManager.has_permission(current_user, Permission.DELETE_VOUCHERS)
    can_delete_own = (RBACManager.has_permission(current_user, Permission.DELETE_OWN_VOUCHERS) 
                     and current_user.get("id") == voucher_owner_id)
    
    if not (can_delete_any or can_delete_own):
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "message": "Insufficient permissions to delete this voucher",
                "required": "DELETE_VOUCHERS permission or ownership + DELETE_OWN_VOUCHERS"
            }
        )
    
    return await voucher_controller.delete_voucher(voucher_id, current_user)

# Admin endpoints

# Get voucher statistics (admin/moderator only)
@router.get("/admin/stats", dependencies=[Depends(require_permission_dep(Permission.VIEW_ANALYTICS)), Depends(normal_rate_limit)])
async def voucher_statistics(current_user: dict = Depends(require_permission_dep(Permission.VIEW_ANALYTICS))):
    """Get voucher statistics (requires VIEW_ANALYTICS permission)"""
    # Use flexible imports
    try:
        from ...shared.database import VoucherDatabase
    except ImportError:
        try:
            from shared.database import VoucherDatabase
        except ImportError:
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(os.path.dirname(current_dir))
            sys.path.append(parent_dir)
            from shared.database import VoucherDatabase
            
    from datetime import datetime, timedelta
    
    vouchers_collection = VoucherDatabase.get_collection("vouchers")
    
    try:
        # Basic statistics
        total_vouchers = await vouchers_collection.count_documents({})
        
        # Active vouchers (not expired)
        current_time = datetime.utcnow()
        active_vouchers = await vouchers_collection.count_documents({
            "$or": [
                {"expiry_date": {"$gt": current_time}},
                {"expiry_date": {"$exists": False}}
            ]
        })
        
        # Expired vouchers
        expired_vouchers = await vouchers_collection.count_documents({
            "expiry_date": {"$lte": current_time}
        })
        
        # Vouchers created in last 30 days
        thirty_days_ago = current_time - timedelta(days=30)
        recent_vouchers = await vouchers_collection.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        
        # Vouchers by category
        category_pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        categories = await vouchers_collection.aggregate(category_pipeline).to_list(length=None)
        
        # Vouchers by type
        type_pipeline = [
            {"$group": {"_id": "$voucher_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        types = await vouchers_collection.aggregate(type_pipeline).to_list(length=None)
        
        # Price statistics
        price_pipeline = [
            {"$match": {"price": {"$gt": 0}}},
            {"$group": {
                "_id": None,
                "avg_price": {"$avg": "$price"},
                "max_price": {"$max": "$price"},
                "min_price": {"$min": "$price"},
                "total_value": {"$sum": "$price"}
            }}
        ]
        price_stats = await vouchers_collection.aggregate(price_pipeline).to_list(length=1)
        price_data = price_stats[0] if price_stats else {
            "avg_price": 0, "max_price": 0, "min_price": 0, "total_value": 0
        }
        
        return {
            "success": True,
            "statistics": {
                "total_vouchers": total_vouchers,
                "active_vouchers": active_vouchers,
                "expired_vouchers": expired_vouchers,
                "recent_vouchers": recent_vouchers,
                "categories": categories,
                "types": types,
                "price_statistics": {
                    "average_price": round(price_data.get("avg_price", 0), 2),
                    "maximum_price": price_data.get("max_price", 0),
                    "minimum_price": price_data.get("min_price", 0),
                    "total_value": price_data.get("total_value", 0)
                }
            }
        }
        
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Error generating voucher statistics",
                "error": str(error)
            }
        )

# Admin: Force update any voucher (super admin only)
@router.put("/admin/{voucher_id}/force-update", dependencies=[Depends(require_permission_dep(Permission.UPDATE_VOUCHERS)), Depends(strict_rate_limit)])
async def admin_force_update_voucher(
    voucher_id: str,
    update_data: VoucherUpdate,
    current_user: dict = Depends(require_permission_dep(Permission.UPDATE_VOUCHERS))
):
    """Force update any voucher (admin only - requires UPDATE_VOUCHERS permission)"""
    return await voucher_controller.update_voucher(voucher_id, update_data, current_user)

# Admin: Force delete any voucher (super admin only)
@router.delete("/admin/{voucher_id}/force-delete", dependencies=[Depends(require_permission_dep(Permission.DELETE_VOUCHERS)), Depends(strict_rate_limit)])
async def admin_force_delete_voucher(
    voucher_id: str,
    current_user: dict = Depends(require_permission_dep(Permission.DELETE_VOUCHERS))
):
    """Force delete any voucher (admin only - requires DELETE_VOUCHERS permission)"""
    return await voucher_controller.delete_voucher(voucher_id, current_user)

# Get user's vouchers (admin or self)
@router.get("/user/{user_id}/vouchers", dependencies=[Depends(get_current_user), Depends(normal_rate_limit)])
async def get_user_vouchers(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Get vouchers posted by a specific user (admin or self)"""
    # Check permission: admin can view any user's vouchers, users can only view their own
    can_view_any = RBACManager.has_permission(current_user, Permission.READ_USERS)
    is_self = current_user.get("id") == user_id
    
    if not (can_view_any or is_self):
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "message": "Access denied - can only view own vouchers",
                "required": "READ_USERS permission or self access"
            }
        )
    
    # Use flexible imports
    try:
        from ...shared.database import VoucherDatabase
    except ImportError:
        try:
            from shared.database import VoucherDatabase
        except ImportError:
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(os.path.dirname(current_dir))
            sys.path.append(parent_dir)
            from shared.database import VoucherDatabase
    
    vouchers_collection = VoucherDatabase.get_collection("vouchers")
    
    try:
        # Get user's vouchers
        vouchers = await vouchers_collection.find(
            {"created_by": user_id}
        ).skip(skip).limit(limit).to_list(length=limit)
        
        # Count total vouchers
        total = await vouchers_collection.count_documents({"created_by": user_id})
        
        # Format response
        for voucher in vouchers:
            voucher["id"] = str(voucher["_id"])
            voucher.pop("_id", None)
        
        return {
            "success": True,
            "vouchers": vouchers,
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
                "has_more": skip + limit < total
            }
        }
        
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Error fetching user vouchers",
                "error": str(error)
            }
        )