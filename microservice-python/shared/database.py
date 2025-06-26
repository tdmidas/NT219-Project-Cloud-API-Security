import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from typing import Optional, Dict, Any
import logging
import urllib.parse
# Database security imports removed

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    databases = {}
    # Security manager removed

    @classmethod
    async def connect_to_mongo(cls, service_name: str, db_uri: str) -> bool:
        """Create database connection for a specific service"""
        try:
            cls.client = AsyncIOMotorClient(
                db_uri,
                maxPoolSize=10,
                minPoolSize=1,
                connectTimeoutMS=5000,
                serverSelectionTimeoutMS=5000,
                retryWrites=True
            )
            
            # Test the connection
            await cls.client.admin.command('ping')
            
            # Parse database name from URI properly
            parsed_uri = urllib.parse.urlparse(db_uri)
            
            # Get database name from path, removing leading slash and query parameters
            if parsed_uri.path and len(parsed_uri.path) > 1:
                db_name = parsed_uri.path[1:]  # Remove leading slash
                # Remove query parameters if present
                if '?' in db_name:
                    db_name = db_name.split('?')[0]
            else:
                # Fallback to service-based name
                db_name = f"voux_{service_name}"
            
            cls.databases[service_name] = cls.client[db_name]
            
            logger.info(f"✅ {service_name.title()} Service connected to MongoDB")
            logger.info(f"📊 Database: {db_name}")
            
            return True
            
        except ConnectionFailure as e:
            logger.error(f"❌ {service_name.title()} Service DB connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
            return False

    @classmethod
    async def close_mongo_connection(cls):
        """Close database connection"""
        if cls.client:
            cls.client.close()
            logger.info("🔌 Database connection closed")

    @classmethod
    def get_database(cls, service_name: str):
        """Get database instance for a service"""
        return cls.databases.get(service_name)
    
    # Secure collection methods removed

# Database connection helpers for each service
class AuthDatabase:
    @staticmethod
    async def connect():
        db_uri = os.getenv("AUTH_DB_URI", "mongodb://localhost:27017/voux_auth")
        return await Database.connect_to_mongo("auth", db_uri)
    
    @staticmethod
    def get_collection(collection_name: str):
        db = Database.get_database("auth")
        return db[collection_name] if db is not None else None
    
    # Secure collection method removed

class UserDatabase:
    @staticmethod
    async def connect():
        db_uri = os.getenv("USER_DB_URI", "mongodb://localhost:27017/voux_users")
        return await Database.connect_to_mongo("user", db_uri)
    
    @staticmethod
    def get_collection(collection_name: str):
        db = Database.get_database("user")
        return db[collection_name] if db is not None else None
    
    # Secure collection method removed

class VoucherDatabase:
    @staticmethod
    async def connect():
        db_uri = os.getenv("VOUCHER_DB_URI", "mongodb+srv://hoangkhanh300105:Khanh2k5%40@mongodb.ng7lw.mongodb.net/Voucher?retryWrites=true&w=majority&appName=MongoDB")
        return await Database.connect_to_mongo("voucher", db_uri)
    
    @staticmethod
    def get_collection(collection_name: str):
        db = Database.get_database("voucher")
        return db[collection_name] if db is not None else None
    
    # Secure collection method removed

class CartDatabase:
    @staticmethod
    async def connect():
        db_uri = os.getenv("CART_DB_URI", "mongodb+srv://hoangkhanh300105:Khanh2k5%40@mongodb.ng7lw.mongodb.net/Voucher?retryWrites=true&w=majority&appName=MongoDB")
        return await Database.connect_to_mongo("cart", db_uri)
    
    @staticmethod
    def get_collection(collection_name: str):
        db = Database.get_database("cart")
        return db[collection_name] if db is not None else None
    
    # Secure collection method removed

# Database event handlers
async def handle_db_error(error: Exception, service_name: str):
    """Handle database errors"""
    logger.error(f"❌ Database error in {service_name}: {error}")

async def handle_db_reconnect(service_name: str, db_uri: str):
    """Handle database reconnection"""
    logger.info(f"🔄 Attempting to reconnect {service_name} to database...")
    success = await Database.connect_to_mongo(service_name, db_uri)
    if success:
        logger.info(f"✅ {service_name} reconnected to database")
    else:
        logger.error(f"❌ Failed to reconnect {service_name} to database")
    return success

# Health check function
async def check_database_health(service_name: str) -> dict:
    """Check database health for a service"""
    try:
        db = Database.get_database(service_name)
        if db is None:
            return {"status": "disconnected", "error": "No database connection"}
        
        # Test connection
        await Database.client.admin.command('ping')
        
        return {
            "status": "connected",
            "database": db.name,
            "collections": await db.list_collection_names()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}