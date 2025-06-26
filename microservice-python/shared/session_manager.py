import secrets
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
from bson import ObjectId
from .database import AuthDatabase
from .models.refresh_token import RefreshToken, RefreshTokenCreate

logger = logging.getLogger(__name__)

class SessionManager:
    """Session management with refresh tokens and blacklisting"""
    
    def __init__(self):
        # In-memory blacklist for immediate token invalidation
        # In production, use Redis for distributed systems
        self.blacklisted_tokens: Set[str] = set()
    
    async def create_refresh_token(self, user_id: str, device_info: Optional[str] = None, ip_address: Optional[str] = None) -> str:
        """Create new refresh token"""
        try:
            # Generate secure refresh token
            refresh_token = secrets.token_urlsafe(64)
            
            # Set expiration (10 minutes để đủ thời gian user thao tác)
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            
            refresh_tokens_collection = AuthDatabase.get_collection("refresh_tokens")
            
            # First, mark existing tokens as revoked (safer than delete)
            try:
                await refresh_tokens_collection.update_many(
                    {"userId": ObjectId(user_id), "isRevoked": False},
                    {"$set": {"isRevoked": True}}
                )
                logger.info(f"Revoked existing refresh tokens for user {user_id}")
            except Exception as e:
                logger.warning(f"Could not revoke existing tokens for user {user_id}: {e}")
                # Continue anyway - not critical
            
            # Create new refresh token record
            token_data = {
                "token": refresh_token,
                "userId": ObjectId(user_id),
                "expiresAt": expires_at,
                "createdAt": datetime.utcnow(),
                "isRevoked": False,
                "deviceInfo": device_info,
                "ipAddress": ip_address
            }
            
            try:
                await refresh_tokens_collection.insert_one(token_data)
                logger.info(f"Created refresh token for user {user_id}, expires at {expires_at}")
            except Exception as e:
                logger.error(f"Failed to insert refresh token: {e}")
                raise Exception(f"Database error creating refresh token: {e}")
            
            return refresh_token
            
        except Exception as error:
            logger.error(f"Error creating refresh token: {error}")
            raise Exception("Failed to create refresh token")
    
    async def validate_refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Validate refresh token and return user info"""
        try:
            # Check if token is blacklisted
            if refresh_token in self.blacklisted_tokens:
                return None
            
            refresh_tokens_collection = AuthDatabase.get_collection("refresh_tokens")
            
            # Find token in database
            token_record = await refresh_tokens_collection.find_one({
                "token": refresh_token,
                "isRevoked": False
            })
            
            if not token_record:
                return None
            
            # Check if token is expired
            if datetime.utcnow() > token_record["expiresAt"]:
                # Delete expired token
                await refresh_tokens_collection.delete_one({"_id": token_record["_id"]})
                return None
            
            # Get user info
            users_collection = AuthDatabase.get_collection("users")
            user = await users_collection.find_one({"_id": token_record["userId"]})
            
            if not user:
                # Delete token for non-existent user
                await refresh_tokens_collection.delete_one({"_id": token_record["_id"]})
                return None
            
            return {
                "user_id": str(user["_id"]),
                "username": user["username"],
                "rbac_role": user.get("rbac_role", "USER"),
                "token_id": str(token_record["_id"])
            }
            
        except Exception as error:
            logger.error(f"Error validating refresh token: {error}")
            return None
    
    async def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Revoke a specific refresh token"""
        try:
            # Add to blacklist for immediate effect
            self.blacklisted_tokens.add(refresh_token)
            
            # Mark as revoked in database
            refresh_tokens_collection = AuthDatabase.get_collection("refresh_tokens")
            result = await refresh_tokens_collection.update_one(
                {"token": refresh_token},
                {"$set": {"isRevoked": True}}
            )
            
            return result.modified_count > 0
            
        except Exception as error:
            logger.error(f"Error revoking refresh token: {error}")
            return False
    
    async def revoke_all_user_tokens(self, user_id: str) -> bool:
        """Revoke all refresh tokens for a user"""
        try:
            refresh_tokens_collection = AuthDatabase.get_collection("refresh_tokens")
            
            # Get all tokens for user to add to blacklist
            user_tokens = await refresh_tokens_collection.find({
                "userId": ObjectId(user_id),
                "isRevoked": False
            }).to_list(length=None)
            
            # Add all tokens to blacklist
            for token_record in user_tokens:
                self.blacklisted_tokens.add(token_record["token"])
            
            # Mark all as revoked in database
            result = await refresh_tokens_collection.update_many(
                {"userId": ObjectId(user_id)},
                {"$set": {"isRevoked": True}}
            )
            
            return True
            
        except Exception as error:
            logger.error(f"Error revoking user tokens: {error}")
            return False
    
    async def cleanup_expired_tokens(self):
        """Clean up expired refresh tokens"""
        try:
            refresh_tokens_collection = AuthDatabase.get_collection("refresh_tokens")
            
            # Delete expired tokens
            result = await refresh_tokens_collection.delete_many({
                "expiresAt": {"$lt": datetime.utcnow()}
            })
            
            logger.info(f"Cleaned up {result.deleted_count} expired refresh tokens")
            
        except Exception as error:
            logger.error(f"Error cleaning up expired tokens: {error}")
    
    def blacklist_access_token(self, access_token: str):
        """Blacklist an access token (for logout)"""
        self.blacklisted_tokens.add(access_token)
    
    def is_access_token_blacklisted(self, access_token: str) -> bool:
        """Check if access token is blacklisted"""
        return access_token in self.blacklisted_tokens
    
    async def get_user_sessions(self, user_id: str) -> list:
        """Get all active sessions for a user"""
        try:
            refresh_tokens_collection = AuthDatabase.get_collection("refresh_tokens")
            
            sessions = await refresh_tokens_collection.find({
                "userId": ObjectId(user_id),
                "isRevoked": False,
                "expiresAt": {"$gt": datetime.utcnow()}
            }).to_list(length=None)
            
            return [{
                "id": str(session["_id"]),
                "device_info": session.get("deviceInfo"),
                "ip_address": session.get("ipAddress"),
                "created_at": session["createdAt"],
                "expires_at": session["expiresAt"]
            } for session in sessions]
            
        except Exception as error:
            logger.error(f"Error getting user sessions: {error}")
            return []

# Create singleton instance
session_manager = SessionManager()