import logging
from typing import Dict, Any
from datetime import datetime
from bson import ObjectId
import asyncio

# Flexible imports
try:
    from ..shared.database import UserDatabase
    from ..shared.event_manager import event_manager
except ImportError:
    try:
        from shared.database import UserDatabase
        from shared.event_manager import event_manager
    except ImportError:
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        sys.path.append(parent_dir)
        
        from shared.database import UserDatabase
        from shared.event_manager import event_manager

logger = logging.getLogger(__name__)

class UserEventHandler:
    """Handle user-related events from Auth Service"""
    
    async def handle_user_registered(self, event_data: Dict[str, Any]):
        """Handle user.registered event - create user copy in voux_users"""
        try:
            logger.info(f"🎉 Processing user.registered event for user: {event_data['event_data']['username']}")
            
            user_data = event_data["event_data"]
            
            # Prepare user document for voux_users database
            user_doc = {
                "_id": ObjectId(user_data["user_id"]),  # Sử dụng cùng _id
                "username": user_data["username"],
                "email": user_data["email"],
                "rbac_role": user_data.get("rbac_role", "USER"),
                "avatar_url": "/default-avatar.png",
                "bio": None,
                "vouchers_posted": 0,
                "vouchers_sold": 0,
                "vouchers_bought": 0,
                "wallet": {
                    "balance": 0.0,
                    "history": []
                },
                "theme": "light",
                "created_at": datetime.fromisoformat(user_data["created_at"].replace('Z', '+00:00')),
                "updated_at": datetime.fromisoformat(user_data["updated_at"].replace('Z', '+00:00')),
                "synced_from_auth": True,  # Flag để biết đây là synced data
                "sync_timestamp": datetime.utcnow()
            }
            
            # Insert vào voux_users database
            users_collection = UserDatabase.get_collection("users")
            
            # Check if user already exists (tránh duplicate)
            existing_user = await users_collection.find_one({"_id": ObjectId(user_data["user_id"])})
            
            if existing_user:
                logger.info(f"👤 User {user_data['username']} already exists in voux_users - updating")
                # Update existing user
                await users_collection.update_one(
                    {"_id": ObjectId(user_data["user_id"])},
                    {"$set": {
                        "username": user_data["username"],
                        "email": user_data["email"],
                        "sync_timestamp": datetime.utcnow()
                    }}
                )
            else:
                logger.info(f"👤 Creating new user {user_data['username']} in voux_users")
                # Insert new user
                await users_collection.insert_one(user_doc)
            
            logger.info(f"✅ Successfully synced user {user_data['username']} to voux_users")
            
        except Exception as e:
            logger.error(f"❌ Failed to handle user.registered event: {e}")
            # Re-raise để message được requeue
            raise
    
    async def process_event(self, message_body: Dict[str, Any]):
        """Route events to appropriate handlers"""
        event_type = message_body.get("event_type")
        
        if event_type == "user.registered":
            await self.handle_user_registered(message_body)
        else:
            logger.warning(f"⚠️ Unknown event type: {event_type}")

# Singleton instance
user_event_handler = UserEventHandler()

async def start_event_consumer():
    """Start consuming events from RabbitMQ"""
    try:
        logger.info("🚀 Starting User Service event consumer...")
        
        # Connect to RabbitMQ with retry
        max_retries = 3
        success = False
        
        for attempt in range(max_retries):
            try:
                success = await event_manager.connect()
                if success:
                    logger.info(f"✅ RabbitMQ connected on attempt {attempt + 1}")
                    break
                else:
                    logger.warning(f"⚠️ RabbitMQ connection attempt {attempt + 1} failed")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)  # Wait before retry
            except Exception as e:
                logger.error(f"❌ RabbitMQ connection error attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    
        if not success:
            logger.error("❌ Failed to connect to RabbitMQ after all retries")
            logger.info("⚠️ User Service will run without event sync")
            return  # Don't crash service, just skip events
        
        # Start consuming user events with a proper timeout approach
        try:
            await event_manager.consume_events(
                queue_name="user_service_queue",
                routing_keys=["user.registered", "user.updated", "user.deleted"],
                callback=user_event_handler.process_event
            )
            
            logger.info("✅ User Service event consumer started successfully")
            
            # Keep consumer running with shorter intervals to avoid blocking
            while True:
                try:
                    await asyncio.sleep(10)  # Check every 10 seconds instead of 60
                    # Add health check to ensure consumer is still alive
                    if not event_manager.connection or event_manager.connection.is_closed:
                        logger.warning("🔄 Event consumer connection lost, attempting to reconnect...")
                        break  # Exit loop to restart consumer
                except asyncio.CancelledError:
                    logger.info("🛑 Event consumer cancelled")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in consumer loop: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"❌ Error setting up event consumer: {e}")
        
    except Exception as e:
        logger.error(f"❌ Event consumer failed: {e}")
        logger.info("⚠️ User Service continuing without event sync")
        # Don't crash the service - just log and continue