import logging
import httpx
import os
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId

# Simple direct imports
try:
    from shared.database import CartDatabase
    
    logging.info("✅ Successfully imported shared modules in cart_controller")
except Exception as e:
    logging.error(f"❌ Import error in cart_controller: {e}")
    raise

logger = logging.getLogger(__name__)

# Pydantic models for cart operations - matching JS backend
class AddToCartRequest(BaseModel):
    voucherId: str  # Match JS backend field name

class RemoveFromCartRequest(BaseModel):
    voucherId: str  # Match JS backend field name

class CartController:
    """Cart management controller - matching JS backend logic"""
    
    def __init__(self):
        self.voucher_service_url = os.getenv("VOUCHER_SERVICE_URL", "http://localhost:3003")
    
    async def get_voucher_details(self, voucher_id: str) -> Optional[Dict[str, Any]]:
        """Get voucher details from voucher service or database"""
        try:
            # First try to get from voucher service
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.voucher_service_url}/api/vouchers/{voucher_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("voucher") if data.get("success") else None
        except Exception as error:
            logger.warning(f"Failed to get voucher from service: {error}")
        
        # Fallback: try to get from voucher database directly
        try:
            from shared.database import VoucherDatabase
            vouchers_collection = VoucherDatabase.get_collection("vouchers")
            
            # Debug: log what we're searching for
            logger.info(f"🔍 Searching for voucher: {voucher_id}")
            
            # Try multiple search strategies
            voucher = None
            
            # Strategy 1: Try by ObjectId if valid
            if ObjectId.is_valid(voucher_id):
                logger.info(f"   📌 Trying ObjectId search: {voucher_id}")
                voucher = await vouchers_collection.find_one({"_id": ObjectId(voucher_id)})
                if voucher:
                    logger.info(f"   ✅ Found by ObjectId")
                    voucher["id"] = str(voucher["_id"])
                    voucher.pop("_id", None)
                    return voucher
            
            # Strategy 2: Try by string id field
            logger.info(f"   📌 Trying string id search: {voucher_id}")
            voucher = await vouchers_collection.find_one({"id": voucher_id})
            if voucher:
                logger.info(f"   ✅ Found by string id field")
                if "_id" in voucher:
                    voucher["id"] = str(voucher["_id"])
                    voucher.pop("_id", None)
                return voucher
            
            # Strategy 3: Try by numeric id if it's a number
            if voucher_id.isdigit():
                logger.info(f"   📌 Trying numeric id search: {int(voucher_id)}")
                voucher = await vouchers_collection.find_one({"id": int(voucher_id)})
                if voucher:
                    logger.info(f"   ✅ Found by numeric id")
                    if "_id" in voucher:
                        voucher["id"] = str(voucher["_id"])
                        voucher.pop("_id", None)
                    return voucher
            
            logger.warning(f"   ❌ Voucher not found with any strategy")
            
            # Debug: Show some sample vouchers in the collection
            sample_vouchers = await vouchers_collection.find({}).limit(3).to_list(length=3)
            logger.info(f"   📊 Sample vouchers in collection:")
            for idx, sample in enumerate(sample_vouchers):
                sample_id = sample.get("id", sample.get("_id", "NO_ID"))
                sample_title = sample.get("title", "NO_TITLE")
                logger.info(f"     {idx+1}. ID: {sample_id} | Title: {sample_title}")
            
        except Exception as error:
            logger.error(f"Error fetching voucher from database: {error}")
        
        return None
    
    async def add_to_cart(self, user_id: str, cart_item: AddToCartRequest) -> Dict[str, Any]:
        """Add item to cart - matching JS backend logic"""
        try:
            # Validate voucherId
            voucher_id = cart_item.voucherId.strip() if cart_item.voucherId else None
            if not voucher_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Voucher ID không hợp lệ!"
                    }
                )
            
            # Find voucher by _id (ObjectId) or id (number/string)
            voucher_details = None
            voucher_object_id = None
            
            # Try by ObjectId first
            if ObjectId.is_valid(voucher_id):
                voucher_details = await self.get_voucher_details(voucher_id)
                if voucher_details:
                    voucher_object_id = voucher_id
            
            # Try by id field if not found
            if not voucher_details:
                # For numeric id
                if voucher_id.isdigit():
                    voucher_details = await self.get_voucher_details(voucher_id)
                    if voucher_details:
                        voucher_object_id = voucher_details.get("id") or voucher_details.get("_id")
            
            if not voucher_details:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": "Voucher không tồn tại hoặc đã bị xóa!"
                    }
                )
            
            carts_collection = CartDatabase.get_collection("carts")
            
            # Find existing cart
            cart = await carts_collection.find_one({"userId": user_id})
            
            if not cart:
                # Create new cart
                cart_data = {
                    "userId": user_id,
                    "vouchers": [{
                        "voucherId": ObjectId(voucher_object_id) if ObjectId.is_valid(voucher_object_id) else voucher_object_id,
                        "quantity": 1
                    }],
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                await carts_collection.insert_one(cart_data)
            else:
                # Check if voucher already exists in cart
                voucher_found = False
                for voucher in cart.get("vouchers", []):
                    if str(voucher["voucherId"]) == str(voucher_object_id):
                        # Increment quantity
                        await carts_collection.update_one(
                            {"userId": user_id, "vouchers.voucherId": voucher["voucherId"]},
                            {
                                "$inc": {"vouchers.$.quantity": 1},
                                "$set": {"updated_at": datetime.utcnow()}
                            }
                        )
                        voucher_found = True
                        break
                
                if not voucher_found:
                    # Add new voucher to cart
                    await carts_collection.update_one(
                        {"userId": user_id},
                        {
                            "$push": {
                                "vouchers": {
                                    "voucherId": ObjectId(voucher_object_id) if ObjectId.is_valid(voucher_object_id) else voucher_object_id,
                                    "quantity": 1
                                }
                            },
                            "$set": {"updated_at": datetime.utcnow()}
                        }
                    )
            
            return {
                "success": True,
                "message": "Đã thêm vào giỏ hàng!"
            }
            
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Add to cart error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi server khi thêm vào giỏ hàng!",
                    "error": str(error)
                }
            )
    
    async def get_cart(self, user_id: str) -> Dict[str, Any]:
        """Get user's cart with populated voucher info - matching JS backend"""
        try:
            carts_collection = CartDatabase.get_collection("carts")
            
            # Find user's cart
            cart = await carts_collection.find_one({"userId": user_id})
            
            if not cart:
                return {
                    "success": True,
                    "cart": {"vouchers": []}
                }
            
            # Get voucher IDs from cart
            voucher_ids = [str(v["voucherId"]) for v in cart.get("vouchers", [])]
            
            if not voucher_ids:
                return {
                    "success": True,
                    "cart": {"vouchers": []}
                }
            
            # Get valid vouchers and filter cart
            valid_vouchers = {}
            valid_voucher_ids = []
            
            for voucher_id in voucher_ids:
                voucher_details = await self.get_voucher_details(voucher_id)
                if voucher_details:
                    valid_vouchers[voucher_id] = voucher_details
                    valid_voucher_ids.append(voucher_id)
            
            # Filter cart vouchers to only include existing ones
            filtered_vouchers = []
            for cart_voucher in cart.get("vouchers", []):
                voucher_id = str(cart_voucher["voucherId"])
                if voucher_id in valid_voucher_ids:
                    # Add populated voucher info
                    cart_voucher_with_info = {
                        "voucherId": valid_vouchers[voucher_id],  # Populated voucher object
                        "quantity": cart_voucher["quantity"]
                    }
                    filtered_vouchers.append(cart_voucher_with_info)
            
            # Update cart if some vouchers were removed
            if len(filtered_vouchers) != len(cart.get("vouchers", [])):
                new_vouchers = []
                for filtered in filtered_vouchers:
                    voucher_id = filtered["voucherId"]["id"]
                    new_vouchers.append({
                        "voucherId": ObjectId(voucher_id) if ObjectId.is_valid(voucher_id) else voucher_id,
                        "quantity": filtered["quantity"]
                    })
                
                await carts_collection.update_one(
                    {"userId": user_id},
                    {
                        "$set": {
                            "vouchers": new_vouchers,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
            
            # Prepare final cart response
            cart_response = {
                "vouchers": filtered_vouchers,
                "userId": user_id,
                "updated_at": cart.get("updated_at", datetime.utcnow())
            }
            
            return {
                "success": True,
                "cart": cart_response
            }
            
        except Exception as error:
            logger.error(f"Get cart error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi lấy giỏ hàng",
                    "error": str(error)
                }
            )
    
    async def remove_from_cart(self, user_id: str, remove_request: RemoveFromCartRequest) -> Dict[str, Any]:
        """Remove item from cart - matching JS backend logic"""
        try:
            voucher_id = remove_request.voucherId
            if not voucher_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Voucher ID không hợp lệ!"
                    }
                )
            
            carts_collection = CartDatabase.get_collection("carts")
            
            # Find user's cart
            cart = await carts_collection.find_one({"userId": user_id})
            if not cart:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": "Không tìm thấy giỏ hàng!"
                    }
                )
            
            # Check initial length
            initial_length = len(cart.get("vouchers", []))
            
            # Remove voucher from cart
            result = await carts_collection.update_one(
                {"userId": user_id},
                {
                    "$pull": {
                        "vouchers": {
                            "voucherId": {
                                "$in": [
                                    ObjectId(voucher_id) if ObjectId.is_valid(voucher_id) else voucher_id,
                                    voucher_id  # Also try string comparison
                                ]
                            }
                        }
                    },
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # Check if something was actually removed
            updated_cart = await carts_collection.find_one({"userId": user_id})
            if updated_cart and len(updated_cart.get("vouchers", [])) == initial_length:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": "Voucher không tồn tại trong giỏ hàng!"
                    }
                )
            
            return {
                "success": True,
                "message": "Đã xóa voucher khỏi giỏ hàng!"
            }
            
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Remove from cart error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi server khi xóa khỏi giỏ hàng!",
                    "error": str(error)
                }
            )

# Create controller instance
cart_controller = CartController() 