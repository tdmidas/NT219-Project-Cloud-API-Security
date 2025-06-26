import logging
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId

# Simple direct imports
try:
    from shared.database import VoucherDatabase
    from shared.secure_db_middleware import (
        require_db_permission, 
        apply_data_masking,
        validate_user_ownership,
        get_user_query_filter,
        DatabaseAuditLogger
    )
    from shared.rbac import Permission
    
    logging.info("✅ Successfully imported shared modules in voucher_controller")
except Exception as e:
    logging.error(f"❌ Import error in voucher_controller: {e}")
    raise

logger = logging.getLogger(__name__)

# Pydantic models for vouchers - updated to match current database schema
class VoucherCreate(BaseModel):
    title: str
    description: Optional[str] = None
    voucher_type: str  # "discount", "gift", "cashback"
    category: str
    price: float = 0.0
    discount_value: Optional[float] = None
    discount_type: Optional[str] = None  # "percentage", "fixed"
    quantity: int = 1
    expiry_date: Optional[datetime] = None
    image_url: Optional[str] = None
    terms_conditions: Optional[str] = None

class VoucherUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    voucher_type: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    discount_value: Optional[float] = None
    discount_type: Optional[str] = None
    quantity: Optional[int] = None
    expiry_date: Optional[datetime] = None
    image_url: Optional[str] = None
    terms_conditions: Optional[str] = None

class VoucherController:
    """Voucher management controller"""
    
    @require_db_permission("vouchers", "read")
    @apply_data_masking("vouchers")
    async def get_all_vouchers(self, skip: int = 0, limit: int = 100, category: Optional[str] = None, current_user: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get all vouchers with pagination and filtering - updated for current database schema"""
        try:
            # Use secure collection with RBAC, RLS, and data masking
            secure_collection = VoucherDatabase.get_secure_collection(
                "vouchers", 
                current_user, 
                Permission.READ_VOUCHERS
            )
            
            # Build query with security filters
            query = get_user_query_filter(current_user, "vouchers")
            
            if category:
                # Support both old and new schema
                category_filter = {
                    "$or": [
                        {"category": category},
                        {"voucherCategory.title": category}
                    ]
                }
                if query:
                    query = {"$and": [query, category_filter]}
                else:
                    query = category_filter
            
            # Get vouchers with pagination and security filters
            cursor = secure_collection.find(query).skip(skip).limit(limit)
            vouchers = await cursor.to_list(length=limit)
            
            # Log database access
            DatabaseAuditLogger.log_access(
                user_id=current_user.get("id") if current_user else None,
                action="read",
                resource="vouchers",
                resource_id="all",
                success=True
            )
            
            # Sort by totalClick descending (like original JS version)
            def get_total_click(voucher):
                total_click = voucher.get("totalClick", "0")
                try:
                    return int(total_click) if total_click else 0
                except (ValueError, TypeError):
                    return 0
            
            vouchers.sort(key=get_total_click, reverse=True)
            
            # Count total vouchers
            total = await vouchers_collection.count_documents(query)
            
            # Format response - keep original structure that frontend expects
            formatted_vouchers = []
            for voucher in vouchers:
                # Convert ObjectId to string
                voucher_dict = dict(voucher)
                voucher_dict["id"] = str(voucher_dict["_id"])
                
                # Ensure all required fields exist with defaults
                if "totalClick" not in voucher_dict:
                    voucher_dict["totalClick"] = "0"
                    
                if "createdAt" not in voucher_dict and "created_at" in voucher_dict:
                    voucher_dict["createdAt"] = voucher_dict["created_at"]
                    
                if "updatedAt" not in voucher_dict and "updated_at" in voucher_dict:
                    voucher_dict["updatedAt"] = voucher_dict["updated_at"]
                    
                if "expiredAt" not in voucher_dict and "expiry_date" in voucher_dict:
                    voucher_dict["expiredAt"] = voucher_dict["expiry_date"]
                
                # Handle nested objects safely
                if "supplier" not in voucher_dict:
                    voucher_dict["supplier"] = {"title": "Unknown", "slug": "unknown"}
                
                if "voucherCategory" not in voucher_dict:
                    category_title = voucher_dict.get("category", "General")
                    voucher_dict["voucherCategory"] = {
                        "id": hash(category_title) % 1000,  # Generate ID from category name
                        "title": category_title
                    }
                
                # Remove _id to avoid confusion
                voucher_dict.pop("_id", None)
                
                formatted_vouchers.append(voucher_dict)
            
            logger.info(f"Found {len(formatted_vouchers)} vouchers (total: {total})")
            
            # Return format that matches frontend expectations
            return {
                "success": True,
                "data": formatted_vouchers,
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "total": total,
                    "has_more": skip + len(formatted_vouchers) < total
                },
                "message": "Lấy danh sách voucher thành công" if formatted_vouchers else "Không có voucher nào"
            }
            
        except Exception as error:
            logger.error(f"Get all vouchers error: {error}")
            # Match frontend expected error format
            return {
                "success": False,
                "data": [],
                "message": "Lỗi server khi lấy danh sách voucher",
                "error": str(error)
            }
    
    async def get_valid_vouchers(self) -> List[Dict[str, Any]]:
        """Get valid vouchers (not expired)"""
        try:
            vouchers_collection = VoucherDatabase.get_collection("vouchers")
            
            # Query for valid vouchers - handle both old and new schema
            current_time = datetime.utcnow()
            query = {
                "$and": [
                    {
                        "$or": [
                            {"quantity": {"$gt": 0}},
                            {"quantity": {"$exists": False}}  # Handle missing quantity
                        ]
                    },
                    {
                        "$or": [
                            {"expiredAt": {"$gt": current_time}},
                            {"expiry_date": {"$gt": current_time}},
                            {"expiredAt": {"$exists": False}},
                            {"expiry_date": {"$exists": False}}
                        ]
                    }
                ]
            }
            
            cursor = vouchers_collection.find(query).sort([("createdAt", -1), ("created_at", -1)])
            vouchers = await cursor.to_list(length=None)
            
            # Format response
            formatted_vouchers = []
            for voucher in vouchers:
                voucher_dict = dict(voucher)
                voucher_dict["id"] = str(voucher_dict["_id"])
                voucher_dict.pop("_id", None)
                
                # Ensure compatibility fields
                if "expiredAt" not in voucher_dict and "expiry_date" in voucher_dict:
                    voucher_dict["expiredAt"] = voucher_dict["expiry_date"]
                
                formatted_vouchers.append(voucher_dict)
            
            # Return proper response format instead of just list
            return {
                "success": True,
                "data": formatted_vouchers,
                "count": len(formatted_vouchers),
                "message": "Lấy voucher hợp lệ thành công" if formatted_vouchers else "Không có voucher hợp lệ"
            }
            
        except Exception as error:
            logger.error(f"Get valid vouchers error: {error}")
            return {
                "success": False,
                "data": [],
                "count": 0,
                "message": "Lỗi khi lấy voucher hợp lệ",
                "error": str(error)
            }
    
    async def get_voucher_by_id(self, voucher_id: str) -> Dict[str, Any]:
        """Get voucher by ID"""
        try:
            vouchers_collection = VoucherDatabase.get_collection("vouchers")
            
            # Validate ObjectId
            if not ObjectId.is_valid(voucher_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "ID voucher không hợp lệ!"
                    }
                )
            
            voucher = await vouchers_collection.find_one({"_id": ObjectId(voucher_id)})
            
            if not voucher:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": "Không tìm thấy voucher!"
                    }
                )
            
            # Format response
            voucher_dict = dict(voucher)
            voucher_dict["id"] = str(voucher_dict["_id"])
            voucher_dict.pop("_id", None)
            
            # Ensure compatibility fields
            if "expiredAt" not in voucher_dict and "expiry_date" in voucher_dict:
                voucher_dict["expiredAt"] = voucher_dict["expiry_date"]
            
            return {
                "success": True,
                "voucher": voucher_dict
            }
            
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Get voucher by ID error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi lấy thông tin voucher!"
                }
            )
    
    async def create_voucher(self, voucher_data: VoucherCreate, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Create new voucher"""
        try:
            vouchers_collection = VoucherDatabase.get_collection("vouchers")
            
            # Prepare voucher data with current database schema
            voucher_dict = {
                "title": voucher_data.title,
                "description": voucher_data.description or "",
                "voucherType": voucher_data.voucher_type,  # Match frontend expectations
                "category": voucher_data.category,
                "voucherCategory": {
                    "id": hash(voucher_data.category) % 1000,
                    "title": voucher_data.category
                },
                "price": voucher_data.price or 0.0,
                "voucherAmount": voucher_data.discount_value or 0,
                "discount_value": voucher_data.discount_value,
                "discount_type": voucher_data.discount_type,
                "quantity": voucher_data.quantity,
                "expiry_date": voucher_data.expiry_date,
                "expiredAt": voucher_data.expiry_date,  # Dual format for compatibility
                "image_url": voucher_data.image_url,
                "terms_conditions": voucher_data.terms_conditions,
                "note": voucher_data.terms_conditions or "",
                "created_by": current_user.get("id"),
                "createdAt": datetime.utcnow(),
                "created_at": datetime.utcnow(),
                "updatedAt": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "status": "active",
                "totalClick": "0",
                "supplier": {
                    "title": "Voux Platform",
                    "slug": "voux"
                },
                "affLink": "",
                "minSpend": 0,
                "maxDiscount": voucher_data.discount_value or 0,
                "voucherCode": "",
                "startAt": None,
                "usageTerms": voucher_data.terms_conditions,
                "useLink": None,
                "avatar": None,
                "payment": None,
                "listApplyLink": ""
            }
            
            # Insert voucher
            result = await vouchers_collection.insert_one(voucher_dict)
            
            if result.inserted_id:
                # Get created voucher
                created_voucher = await vouchers_collection.find_one({"_id": result.inserted_id})
                created_voucher["id"] = str(created_voucher["_id"])
                created_voucher.pop("_id", None)
                
                return {
                    "success": True,
                    "message": "Tạo voucher thành công! 🎉",
                    "voucher": created_voucher
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "success": False,
                        "message": "Lỗi khi tạo voucher!"
                    }
                )
                
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Create voucher error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi server khi tạo voucher!"
                }
            )
    
    async def update_voucher(self, voucher_id: str, update_data: VoucherUpdate, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Update voucher"""
        try:
            vouchers_collection = VoucherDatabase.get_collection("vouchers")
            
            # Validate ObjectId
            if not ObjectId.is_valid(voucher_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "ID voucher không hợp lệ!"
                    }
                )
            
            # Check if voucher exists
            existing_voucher = await vouchers_collection.find_one({"_id": ObjectId(voucher_id)})
            if not existing_voucher:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": "Không tìm thấy voucher!"
                    }
                )
            
            # Check permission (owner or admin)
            if (existing_voucher.get("created_by") != current_user.get("id") and 
                not current_user.get("admin", False)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "message": "Bạn không có quyền cập nhật voucher này!"
                    }
                )
            
            # Prepare update data with dual schema support
            update_fields = {}
            update_dict = update_data.dict(exclude_unset=True)
            
            for field, value in update_dict.items():
                if value is not None:
                    update_fields[field] = value
                    
                    # Handle schema mapping
                    if field == "voucher_type":
                        update_fields["voucherType"] = value
                    elif field == "discount_value":
                        update_fields["voucherAmount"] = value
                    elif field == "expiry_date":
                        update_fields["expiredAt"] = value
                    elif field == "category":
                        update_fields["voucherCategory"] = {
                            "id": hash(value) % 1000,
                            "title": value
                        }
            
            # Add updated timestamp
            update_fields["updated_at"] = datetime.utcnow()
            update_fields["updatedAt"] = datetime.utcnow()
            
            # Update voucher
            result = await vouchers_collection.update_one(
                {"_id": ObjectId(voucher_id)},
                {"$set": update_fields}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Không có thay đổi nào được thực hiện!"
                    }
                )
            
            # Get updated voucher
            updated_voucher = await vouchers_collection.find_one({"_id": ObjectId(voucher_id)})
            updated_voucher["id"] = str(updated_voucher["_id"])
            updated_voucher.pop("_id", None)
            
            return {
                "success": True,
                "message": "Cập nhật voucher thành công! 🎉",
                "voucher": updated_voucher
            }
            
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Update voucher error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi cập nhật voucher!"
                }
            )
    
    async def delete_voucher(self, voucher_id: str, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Delete voucher"""
        try:
            vouchers_collection = VoucherDatabase.get_collection("vouchers")
            
            # Validate ObjectId
            if not ObjectId.is_valid(voucher_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "ID voucher không hợp lệ!"
                    }
                )
            
            # Check if voucher exists
            voucher = await vouchers_collection.find_one({"_id": ObjectId(voucher_id)})
            if not voucher:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": "Không tìm thấy voucher!"
                    }
                )
            
            # Check permission (owner or admin)
            if (voucher.get("created_by") != current_user.get("id") and 
                not current_user.get("admin", False)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "message": "Bạn không có quyền xóa voucher này!"
                    }
                )
            
            # Delete voucher
            result = await vouchers_collection.delete_one({"_id": ObjectId(voucher_id)})
            
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "success": False,
                        "message": "Lỗi khi xóa voucher!"
                    }
                )
            
            return {
                "success": True,
                "message": f"Đã xóa voucher '{voucher['title']}' thành công!"
            }
            
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Delete voucher error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi xóa voucher!"
                }
            )
    
    async def search_vouchers(self, query: str, category: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Search vouchers by title, description, or category"""
        try:
            vouchers_collection = VoucherDatabase.get_collection("vouchers")
            
            # Build search query - handle both old and new schema
            search_conditions = [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"category": {"$regex": query, "$options": "i"}},
                {"voucherCategory.title": {"$regex": query, "$options": "i"}},
                {"note": {"$regex": query, "$options": "i"}}
            ]
            
            search_query = {"$or": search_conditions}
            
            # Add category filter if specified
            if category:
                search_query["$and"] = [
                    search_query,
                    {
                        "$or": [
                            {"category": category},
                            {"voucherCategory.title": category}
                        ]
                    }
                ]
            
            # Search vouchers
            cursor = vouchers_collection.find(search_query).limit(limit).sort([("createdAt", -1), ("created_at", -1)])
            vouchers = await cursor.to_list(length=limit)
            
            # Format response
            formatted_vouchers = []
            for voucher in vouchers:
                voucher_dict = dict(voucher)
                voucher_dict["id"] = str(voucher_dict["_id"])
                voucher_dict.pop("_id", None)
                
                # Ensure compatibility fields
                if "expiredAt" not in voucher_dict and "expiry_date" in voucher_dict:
                    voucher_dict["expiredAt"] = voucher_dict["expiry_date"]
                
                formatted_vouchers.append(voucher_dict)
            
            return {
                "success": True,
                "query": query,
                "category": category,
                "results": formatted_vouchers,
                "count": len(formatted_vouchers)
            }
            
        except Exception as error:
            logger.error(f"Search vouchers error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi tìm kiếm voucher!"
                }
            )
    
    async def get_categories(self) -> Dict[str, Any]:
        """Get all voucher categories"""
        try:
            vouchers_collection = VoucherDatabase.get_collection("vouchers")
            
            # Get distinct categories from both old and new schema
            categories_old = await vouchers_collection.distinct("category")
            categories_new = await vouchers_collection.distinct("voucherCategory.title")
            
            # Combine and deduplicate
            all_categories = list(set(categories_old + categories_new))
            all_categories = [cat for cat in all_categories if cat]  # Remove empty/null values
            all_categories.sort()
            
            # Count vouchers per category
            category_counts = {}
            for category in all_categories:
                count = await vouchers_collection.count_documents({
                    "$or": [
                        {"category": category},
                        {"voucherCategory.title": category}
                    ]
                })
                category_counts[category] = count
            
            return {
                "success": True,
                "categories": all_categories,
                "category_counts": category_counts,
                "total_categories": len(all_categories)
            }
            
        except Exception as error:
            logger.error(f"Get categories error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi lấy danh mục voucher!"
                }
            )

# Create controller instance
voucher_controller = VoucherController()