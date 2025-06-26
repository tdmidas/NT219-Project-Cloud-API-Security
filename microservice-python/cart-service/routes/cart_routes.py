from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional

# Flexible imports
try:
    # Try relative imports first (when running as module)
    from ..controllers.cart_controller import (
        cart_controller, 
        AddToCartRequest, 
        RemoveFromCartRequest
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
        from cart_service.controllers.cart_controller import (
            cart_controller, 
            AddToCartRequest, 
            RemoveFromCartRequest
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
        
        from controllers.cart_controller import (
            cart_controller, 
            AddToCartRequest, 
            RemoveFromCartRequest
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

# Main cart endpoints - matching JS backend exactly

# Get user's cart
@router.get("/", dependencies=[Depends(require_permission_dep(Permission.READ_OWN_CART)), Depends(normal_rate_limit)])
async def get_cart(current_user: dict = Depends(get_current_user)):
    """Get user's cart - matching JS backend"""
    user_id = current_user.get("id")
    return await cart_controller.get_cart(user_id)

# Add item to cart
@router.post("/add", dependencies=[Depends(require_permission_dep(Permission.MANAGE_OWN_CART)), Depends(normal_rate_limit)])
async def add_to_cart(
    cart_item: AddToCartRequest,
    current_user: dict = Depends(require_permission_dep(Permission.MANAGE_OWN_CART))
):
    """Add voucher to cart - matching JS backend with { voucherId } body"""
    user_id = current_user.get("id")
    return await cart_controller.add_to_cart(user_id, cart_item)

# Remove item from cart
@router.post("/remove", dependencies=[Depends(require_permission_dep(Permission.MANAGE_OWN_CART)), Depends(normal_rate_limit)])
async def remove_from_cart(
    remove_request: RemoveFromCartRequest,
    current_user: dict = Depends(require_permission_dep(Permission.MANAGE_OWN_CART))
):
    """Remove voucher from cart - matching JS backend with { voucherId } body"""
    user_id = current_user.get("id")
    return await cart_controller.remove_from_cart(user_id, remove_request)

# Additional convenience endpoints (not in JS backend but useful)

# Update cart item quantity (keeping this for potential future use)
@router.put("/update/{voucher_id}", dependencies=[Depends(require_permission_dep(Permission.MANAGE_OWN_CART)), Depends(normal_rate_limit)])
async def update_cart_item_quantity(
    voucher_id: str,
    quantity: int = Query(..., ge=1, description="New quantity"),
    current_user: dict = Depends(require_permission_dep(Permission.MANAGE_OWN_CART))
):
    """Update cart item quantity (convenience endpoint, not in JS backend)"""
    user_id = current_user.get("id")
    
    if quantity <= 0:
        # Remove item if quantity is 0 or negative
        remove_request = RemoveFromCartRequest(voucherId=voucher_id)
        return await cart_controller.remove_from_cart(user_id, remove_request)
    
    # For now, we'll implement this by removing and re-adding
    # In a real implementation, you'd want a proper update method
    try:
        # First remove the item
        remove_request = RemoveFromCartRequest(voucherId=voucher_id)
        await cart_controller.remove_from_cart(user_id, remove_request)
        
        # Then add it back with the new quantity
        for _ in range(quantity):
            add_request = AddToCartRequest(voucherId=voucher_id)
            await cart_controller.add_to_cart(user_id, add_request)
        
        return {
            "success": True,
            "message": f"Đã cập nhật số lượng voucher thành {quantity}!"
        }
        
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Lỗi khi cập nhật số lượng voucher!",
                "error": str(error)
            }
        )

# Clear entire cart (convenience endpoint)
@router.delete("/clear", dependencies=[Depends(require_permission_dep(Permission.MANAGE_OWN_CART)), Depends(strict_rate_limit)])
async def clear_cart(current_user: dict = Depends(require_permission_dep(Permission.MANAGE_OWN_CART))):
    """Clear user's entire cart (convenience endpoint, not in JS backend)"""
    user_id = current_user.get("id")
    
    try:
        # Get current cart
        cart_data = await cart_controller.get_cart(user_id)
        cart = cart_data.get("cart", {})
        vouchers = cart.get("vouchers", [])
        
        # Remove each voucher
        for voucher_item in vouchers:
            voucher_id = voucher_item.get("voucherId", {}).get("id")
            if voucher_id:
                remove_request = RemoveFromCartRequest(voucherId=voucher_id)
                await cart_controller.remove_from_cart(user_id, remove_request)
        
        return {
            "success": True,
            "message": "Đã xóa tất cả voucher khỏi giỏ hàng!"
        }
        
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Lỗi khi xóa giỏ hàng!",
                "error": str(error)
            }
        )

# Cart summary endpoint
@router.get("/summary", dependencies=[Depends(require_permission_dep(Permission.READ_OWN_CART)), Depends(normal_rate_limit)])
async def cart_summary(current_user: dict = Depends(get_current_user)):
    """Get cart summary with totals"""
    user_id = current_user.get("id")
    
    try:
        cart_data = await cart_controller.get_cart(user_id)
        cart = cart_data.get("cart", {})
        vouchers = cart.get("vouchers", [])
        
        # Calculate summary
        total_items = len(vouchers)
        total_quantity = sum(item.get("quantity", 0) for item in vouchers)
        total_amount = sum(
            item.get("voucherId", {}).get("price", 0) * item.get("quantity", 0) 
            for item in vouchers
        )
        
        return {
            "success": True,
            "summary": {
                "user_id": user_id,
                "total_items": total_items,
                "total_quantity": total_quantity, 
                "total_amount": total_amount,
                "updated_at": cart.get("updated_at")
            }
        }
        
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Lỗi khi lấy tóm tắt giỏ hàng!",
                "error": str(error)
            }
        )

# Admin endpoints

# Admin: Get any user's cart
@router.get("/admin/{user_id}", dependencies=[Depends(require_permission_dep(Permission.READ_USERS)), Depends(normal_rate_limit)])
async def admin_get_user_cart(
    user_id: str,
    current_user: dict = Depends(require_permission_dep(Permission.READ_USERS))
):
    """Get any user's cart (admin only)"""
    return await cart_controller.get_cart(user_id)

# Admin: Clear any user's cart
@router.delete("/admin/{user_id}/clear", dependencies=[Depends(require_permission_dep(Permission.UPDATE_USERS)), Depends(strict_rate_limit)])
async def admin_clear_user_cart(
    user_id: str,
    current_user: dict = Depends(require_permission_dep(Permission.UPDATE_USERS))
):
    """Clear any user's cart (admin only)"""
    try:
        # Get user's cart first
        cart_data = await cart_controller.get_cart(user_id)
        cart = cart_data.get("cart", {})
        vouchers = cart.get("vouchers", [])
        
        # Remove each voucher
        for voucher_item in vouchers:
            voucher_id = voucher_item.get("voucherId", {}).get("id")
            if voucher_id:
                remove_request = RemoveFromCartRequest(voucherId=voucher_id)
                await cart_controller.remove_from_cart(user_id, remove_request)
        
        return {
            "success": True,
            "message": f"Đã xóa giỏ hàng của user {user_id}!"
        }
        
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Lỗi khi xóa giỏ hàng!",
                "error": str(error)
            }
        )

# Admin: Cart analytics
@router.get("/admin/analytics", dependencies=[Depends(require_permission_dep(Permission.VIEW_ANALYTICS)), Depends(normal_rate_limit)])
async def cart_analytics(current_user: dict = Depends(require_permission_dep(Permission.VIEW_ANALYTICS))):
    """Get cart analytics (admin only)"""
    try:
        # Use flexible imports
        try:
            from ...shared.database import CartDatabase
        except ImportError:
            try:
                from shared.database import CartDatabase
            except ImportError:
                import sys
                import os
                current_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(os.path.dirname(current_dir))
                sys.path.append(parent_dir)
                from shared.database import CartDatabase
        
        from datetime import datetime, timedelta
        
        carts_collection = CartDatabase.get_collection("carts")
        
        # Basic analytics
        total_carts = await carts_collection.count_documents({})
        
        # Active carts (with items)
        active_carts = await carts_collection.count_documents({
            "vouchers": {"$exists": True, "$ne": []}
        })
        
        # Empty carts
        empty_carts = total_carts - active_carts
        
        # Recent carts (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_carts = await carts_collection.count_documents({
            "updated_at": {"$gte": seven_days_ago}
        })
        
        # Most popular vouchers in carts
        pipeline = [
            {"$unwind": "$vouchers"},
            {"$group": {
                "_id": "$vouchers.voucherId",
                "count": {"$sum": "$vouchers.quantity"},
                "users": {"$addToSet": "$userId"}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        popular_vouchers = await carts_collection.aggregate(pipeline).to_list(length=10)
        
        return {
            "success": True,
            "analytics": {
                "total_carts": total_carts,
                "active_carts": active_carts,
                "empty_carts": empty_carts,
                "recent_carts": recent_carts,
                "popular_vouchers": popular_vouchers
            }
        }
        
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Lỗi khi lấy analytics giỏ hàng!",
                "error": str(error)
            }
        )

# Admin: Clean up empty carts
@router.delete("/admin/cleanup/empty", dependencies=[Depends(require_permission_dep(Permission.MANAGE_SYSTEM)), Depends(strict_rate_limit)])
async def admin_cleanup_empty_carts(current_user: dict = Depends(require_permission_dep(Permission.MANAGE_SYSTEM))):
    """Clean up empty carts (admin only)"""
    try:
        # Use flexible imports  
        try:
            from ...shared.database import CartDatabase
        except ImportError:
            try:
                from shared.database import CartDatabase
            except ImportError:
                import sys
                import os
                current_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(os.path.dirname(current_dir))
                sys.path.append(parent_dir)
                from shared.database import CartDatabase
        
        carts_collection = CartDatabase.get_collection("carts")
        
        # Delete empty carts
        result = await carts_collection.delete_many({
            "$or": [
                {"vouchers": {"$exists": False}},
                {"vouchers": {"$eq": []}},
                {"vouchers": {"$size": 0}}
            ]
        })
        
        return {
            "success": True,
            "message": f"Đã xóa {result.deleted_count} giỏ hàng trống!"
        }
        
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Lỗi khi dọn dẹp giỏ hàng!",
                "error": str(error)
            }
        ) 