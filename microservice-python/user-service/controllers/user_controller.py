import logging
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status, UploadFile
from pydantic import BaseModel, EmailStr
from datetime import datetime
from bson import ObjectId

# Simple direct imports
try:
    from shared.database import UserDatabase
    from shared.models.user import User, UserUpdate, UserResponse
    # Secure DB middleware imports removed
    from shared.rbac import RBACManager, Permission, Role
    
    logging.info("✅ Successfully imported shared modules in user_controller")
except Exception as e:
    logging.error(f"❌ Import error in user_controller: {e}")
    raise

logger = logging.getLogger(__name__)

# Pydantic models for requests
class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    theme: Optional[str] = None

class WalletTransaction(BaseModel):
    amount: float
    transaction_type: str  # deposit, withdrawal, purchase, sale
    description: Optional[str] = None

class UserController:
    """User management controller"""
    
    async def get_all_users(self, skip: int = 0, limit: int = 100, current_user: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get all users (admin only)"""
        try:
            # Get users collection directly
            users_collection = UserDatabase.get_collection("users")
            
            # Get users with pagination
            cursor = users_collection.find({}).skip(skip).limit(limit)
            users = await cursor.to_list(length=limit)
            
            # Database access logging removed
            
            # Convert ObjectIds to strings and prepare safe user data
            safe_users = []
            for user in users:
                safe_user = {
                    "id": str(user["_id"]),
                    "username": user.get("username"),
                    "email": user.get("email"),
                    "rbac_role": user.get("rbac_role", "USER"),
                    "avatar_url": user.get("avatar_url", "/default-avatar.png"),
                    "bio": user.get("bio"),
                    "vouchers_posted": user.get("vouchers_posted", 0),
                    "vouchers_sold": user.get("vouchers_sold", 0),
                    "vouchers_bought": user.get("vouchers_bought", 0),
                    "wallet": {
                        "balance": user.get("wallet", {}).get("balance", 0.0)
                    },
                    "theme": user.get("theme", "light"),
                    "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
                    "updated_at": user.get("updated_at").isoformat() if user.get("updated_at") else None,
                    "last_login": user.get("last_login").isoformat() if user.get("last_login") else None,
                    "synced_from_auth": user.get("synced_from_auth", False)
                }
                safe_users.append(safe_user)
            
            # Get total count
            total_count = await users_collection.count_documents({})
            
            return {
                "success": True,
                "users": safe_users,
                "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "total": total_count,
                    "has_more": skip + limit < total_count
                }
            }
            
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Get all users error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi lấy danh sách người dùng!"
                }
            )
    
    async def get_user_profile(self, user_id: str, current_user: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get user profile by ID"""
        try:
            # Validate ObjectId
            if not ObjectId.is_valid(user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Invalid user ID format!"
                    }
                )
            
            # Get users collection directly
            users_collection = UserDatabase.get_collection("users")
            
            # Find user by ID
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": "Không tìm thấy người dùng!"
                    }
                )
            
            # Database access logging removed
            
            # Prepare safe profile data (exclude sensitive information)
            safe_profile = {
                "id": str(user["_id"]),
                "username": user.get("username"),
                "email": user.get("email"),
                "rbac_role": user.get("rbac_role", "USER"),
                "avatar_url": user.get("avatar_url", "/default-avatar.png"),
                "bio": user.get("bio"),
                "vouchers_posted": user.get("vouchers_posted", 0),
                "vouchers_sold": user.get("vouchers_sold", 0),
                "vouchers_bought": user.get("vouchers_bought", 0),
                "wallet": {
                    "balance": user.get("wallet", {}).get("balance", 0.0)
                },
                "theme": user.get("theme", "light"),
                "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
                "updated_at": user.get("updated_at").isoformat() if user.get("updated_at") else None,
                "last_login": user.get("last_login").isoformat() if user.get("last_login") else None,
                "synced_from_auth": user.get("synced_from_auth", False)
            }
            
            return {
                "success": True,
                "user": safe_profile
            }
            
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Get user profile error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi lấy thông tin người dùng!"
                }
            )
    
    async def get_my_profile(self, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Get current user's detailed profile"""
        user_id = current_user.get("id")
        return await self.get_user_profile(user_id)
    
    async def update_user_profile(self, user_id: str, update_data: UserProfileUpdate, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        try:
            # Basic access check - user can only update their own profile or have admin permission
            if current_user.get("id") != user_id and not RBACManager.has_permission(current_user, Permission.ADMIN_ACCESS):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "message": "Bạn không có quyền cập nhật profile này!"
                    }
                )
            
            # Validate ObjectId
            if not ObjectId.is_valid(user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "ID người dùng không hợp lệ!"
                    }
                )
            
            # Get users collection directly
            users_collection = UserDatabase.get_collection("users")
            
            # Check if user exists
            existing_user = await users_collection.find_one({"_id": ObjectId(user_id)})
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": "Không tìm thấy người dùng!"
                    }
                )
            
            # Prepare update data
            update_fields = {}
            update_dict = update_data.dict(exclude_unset=True)
            
            for field, value in update_dict.items():
                if value is not None:
                    update_fields[field] = value
            
            # Add updated timestamp
            update_fields["updated_at"] = datetime.utcnow()
            
            # Check username uniqueness if updating
            if "username" in update_fields:
                existing_username = await users_collection.find_one({
                    "username": update_fields["username"],
                    "_id": {"$ne": ObjectId(user_id)}
                })
                if existing_username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "success": False,
                            "message": "Tên đăng nhập đã được sử dụng!"
                        }
                    )
            
            # Check email uniqueness if updating
            if "email" in update_fields:
                existing_email = await users_collection.find_one({
                    "email": update_fields["email"],
                    "_id": {"$ne": ObjectId(user_id)}
                })
                if existing_email:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "success": False,
                            "message": "Email đã được sử dụng!"
                        }
                    )
            
            # Update user
            result = await users_collection.update_one(
                {"_id": ObjectId(user_id)},
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
            
            # Get updated user
            updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
            updated_user.pop("password", None)
            updated_user["id"] = str(updated_user["_id"])
            
            return {
                "success": True,
                "message": "Cập nhật profile thành công! 🎉",
                "user": updated_user
            }
            
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Update user profile error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi cập nhật profile!"
                }
            )
    
    async def delete_user(self, user_id: str, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Delete user (admin only)"""
        try:
            # Check admin permission
            if not RBACManager.has_permission(current_user, Permission.ADMIN_ACCESS):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "message": "Chỉ admin mới có thể xóa người dùng!"
                    }
                )
            
            users_collection = UserDatabase.get_collection("users")
            
            # Validate ObjectId
            if not ObjectId.is_valid(user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "ID người dùng không hợp lệ!"
                    }
                )
            
            # Check if user exists
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": "Không tìm thấy người dùng!"
                    }
                )
            
            # Prevent self-deletion
            if current_user.get("id") == user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Bạn không thể xóa tài khoản của chính mình!"
                    }
                )
            
            # Delete user
            result = await users_collection.delete_one({"_id": ObjectId(user_id)})
            
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "success": False,
                        "message": "Lỗi khi xóa người dùng!"
                    }
                )
            
            return {
                "success": True,
                "message": f"Đã xóa người dùng {user['username']} thành công!"
            }
            
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Delete user error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi xóa người dùng!"
                }
            )
    
    async def manage_wallet(self, user_id: str, transaction: WalletTransaction, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Manage user wallet transactions"""
        try:
            # Check permission
            if current_user.get("id") != user_id and not RBACManager.has_permission(current_user, Permission.ADMIN_ACCESS):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "message": "Bạn không có quyền thao tác với ví này!"
                    }
                )
            
            users_collection = UserDatabase.get_collection("users")
            
            # Validate ObjectId
            if not ObjectId.is_valid(user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "ID người dùng không hợp lệ!"
                    }
                )
            
            user = await users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": "Không tìm thấy người dùng!"
                    }
                )
            
            # Get current wallet
            wallet = user.get("wallet", {"balance": 0.0, "history": []})
            current_balance = wallet.get("balance", 0.0)
            
            # Validate transaction
            if transaction.transaction_type in ["withdrawal", "purchase"] and current_balance < transaction.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Số dư không đủ để thực hiện giao dịch!"
                    }
                )
            
            # Calculate new balance
            if transaction.transaction_type in ["deposit", "sale"]:
                new_balance = current_balance + transaction.amount
            else:  # withdrawal, purchase
                new_balance = current_balance - transaction.amount
            
            # Create transaction record
            transaction_record = {
                "amount": transaction.amount,
                "type": transaction.transaction_type,
                "description": transaction.description,
                "date": datetime.utcnow()
            }
            
            # Update wallet
            updated_wallet = {
                "balance": new_balance,
                "history": wallet.get("history", []) + [transaction_record]
            }
            
            # Update user
            result = await users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "wallet": updated_wallet,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "success": False,
                        "message": "Lỗi khi cập nhật ví!"
                    }
                )
            
            return {
                "success": True,
                "message": "Giao dịch thành công! 💰",
                "transaction": transaction_record,
                "wallet": {
                    "previous_balance": current_balance,
                    "new_balance": new_balance,
                    "amount": transaction.amount,
                    "type": transaction.transaction_type
                }
            }
            
        except HTTPException:
            raise
        except Exception as error:
            logger.error(f"Wallet management error: {error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Lỗi khi thao tác với ví!"
                }
            )

# Create controller instance
user_controller = UserController()