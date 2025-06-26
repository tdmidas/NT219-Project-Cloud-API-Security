#!/usr/bin/env python3
"""
Debug script for Voucher Service
- Check database connection
- Check if vouchers exist
- Add sample vouchers if database is empty
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Multiple MongoDB endpoints to test
MONGODB_ENDPOINTS = [
    {
        "name": "Endpoint 1 (minhdai)",
        "uri": "mongodb+srv://minhdai:mutoyugi@cluster0.xqhnrnv.mongodb.net/voux_vouchers?retryWrites=true&w=majority&appName=Cluster0"
    },
    {
        "name": "Endpoint 2 (hoangkhanh - voux_vouchers)",
        "uri": "mongodb+srv://hoangkhanh300105:Khanh2k5%40@mongodb.ng7lw.mongodb.net/voux_vouchers?retryWrites=true&w=majority&appName=MongoDB"
    },
    {
        "name": "Endpoint 3 (hoangkhanh - Voucher)",
        "uri": "mongodb+srv://hoangkhanh300105:Khanh2k5%40@mongodb.ng7lw.mongodb.net/Voucher?retryWrites=true&w=majority&appName=MongoDB"
    },
    {
        "name": "Localhost (fallback)",
        "uri": "mongodb://localhost:27017/voux_vouchers"
    }
]

async def check_single_database(endpoint_info):
    """Check a single MongoDB endpoint"""
    name = endpoint_info["name"]
    db_uri = endpoint_info["uri"]
    
    print(f"\n🔍 Testing {name}")
    print(f"📍 URI: {db_uri}")
    
    try:
        client = AsyncIOMotorClient(db_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Connection successful")
        
        # Get database name from URI
        import urllib.parse
        parsed_uri = urllib.parse.urlparse(db_uri)
        
        if parsed_uri.path and len(parsed_uri.path) > 1:
            db_name = parsed_uri.path[1:]  # Remove leading slash
            if '?' in db_name:
                db_name = db_name.split('?')[0]
        else:
            db_name = "voux_vouchers"
        
        print(f"📊 Database name: {db_name}")
        
        db = client[db_name]
        
        # List all collections
        collections = await db.list_collection_names()
        print(f"📁 Collections: {collections}")
        
        # Check vouchers collection
        vouchers_collection = db["vouchers"]
        voucher_count = await vouchers_collection.count_documents({})
        print(f"📋 Vouchers in database: {voucher_count}")
        
        if voucher_count > 0:
            # Show sample vouchers
            sample_vouchers = await vouchers_collection.find({}).limit(3).to_list(length=3)
            print("📄 Sample vouchers:")
            for voucher in sample_vouchers:
                title = voucher.get('title', 'No title')
                category = voucher.get('category', 'No category')
                price = voucher.get('price', 0)
                print(f"  - {title} | {category} | {price} VND")
        
        return {
            "success": True,
            "client": client,
            "db": db,
            "vouchers_collection": vouchers_collection,
            "voucher_count": voucher_count,
            "endpoint_info": endpoint_info
        }
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "endpoint_info": endpoint_info
        }

async def check_all_databases():
    """Check all MongoDB endpoints"""
    print("🔍 Testing Multiple MongoDB Endpoints")
    print("=" * 60)
    
    results = []
    
    for endpoint_info in MONGODB_ENDPOINTS:
        result = await check_single_database(endpoint_info)
        results.append(result)
        
        # Close client if opened and successful
        if result.get("success") and result.get("client"):
            try:
                await result["client"].close()
            except Exception as e:
                print(f"⚠️ Error closing connection: {e}")
    
    return results

async def find_best_endpoint():
    """Find the endpoint with the most vouchers"""
    results = await check_all_databases()
    
    print("\n📊 Summary:")
    print("=" * 60)
    
    best_endpoint = None
    max_vouchers = -1
    
    for result in results:
        name = result["endpoint_info"]["name"]
        if result["success"]:
            voucher_count = result["voucher_count"]
            print(f"✅ {name}: {voucher_count} vouchers")
            
            if voucher_count > max_vouchers:
                max_vouchers = voucher_count
                best_endpoint = result["endpoint_info"]
        else:
            print(f"❌ {name}: Failed - {result['error']}")
    
    if best_endpoint:
        print(f"\n🏆 Best endpoint: {best_endpoint['name']} with {max_vouchers} vouchers")
        return best_endpoint
    else:
        print("\n❌ No working endpoints found!")
        return None

async def add_sample_vouchers(vouchers_collection):
    """Add sample vouchers to database"""
    print("🎫 Adding sample vouchers...")
    
    sample_vouchers = [
        {
            "title": "Pizza Hut - Giảm 30%",
            "description": "Giảm 30% cho tất cả pizza size L",
            "voucher_type": "discount",
            "category": "food",
            "price": 50000,
            "discount_value": 30,
            "discount_type": "percentage",
            "quantity": 100,
            "expiry_date": datetime.utcnow() + timedelta(days=30),
            "image_url": "/vouchers/pizza-hut.png",
            "terms_conditions": "Áp dụng từ thứ 2 đến thứ 6",
            "created_by": str(ObjectId()),  # Dummy user ID
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active"
        },
        {
            "title": "Grab Food - Freeship",
            "description": "Miễn phí ship cho đơn từ 100k",
            "voucher_type": "discount",
            "category": "delivery",
            "price": 0,
            "discount_value": 25000,
            "discount_type": "fixed",
            "quantity": 50,
            "expiry_date": datetime.utcnow() + timedelta(days=15),
            "image_url": "/vouchers/grab-food.png",
            "terms_conditions": "Áp dụng trong bán kính 5km",
            "created_by": str(ObjectId()),  # Dummy user ID
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active"
        },
        {
            "title": "Highlands Coffee - Buy 1 Get 1",
            "description": "Mua 1 tặng 1 cho tất cả đồ uống",
            "voucher_type": "gift",
            "category": "beverage",
            "price": 75000,
            "discount_value": 50,
            "discount_type": "percentage",
            "quantity": 200,
            "expiry_date": datetime.utcnow() + timedelta(days=45),
            "image_url": "/vouchers/highlands.png",
            "terms_conditions": "Không áp dụng với combo",
            "created_by": str(ObjectId()),  # Dummy user ID
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active"
        },
        {
            "title": "Shopee - Voucher 100k",
            "description": "Giảm 100k cho đơn hàng từ 500k",
            "voucher_type": "cashback",
            "category": "shopping",
            "price": 20000,
            "discount_value": 100000,
            "discount_type": "fixed",
            "quantity": 1000,
            "expiry_date": datetime.utcnow() + timedelta(days=7),
            "image_url": "/vouchers/shopee.png",
            "terms_conditions": "Áp dụng cho sản phẩm thời trang",
            "created_by": str(ObjectId()),  # Dummy user ID
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active"
        },
        {
            "title": "CGV Cinema - Vé 50k",
            "description": "Vé xem phim chỉ 50k mọi suất chiếu",
            "voucher_type": "discount",
            "category": "entertainment",
            "price": 30000,
            "discount_value": 70000,
            "discount_type": "fixed",
            "quantity": 300,
            "expiry_date": datetime.utcnow() + timedelta(days=60),
            "image_url": "/vouchers/cgv.png",
            "terms_conditions": "Không áp dụng vào cuối tuần",
            "created_by": str(ObjectId()),  # Dummy user ID
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": "active"
        }
    ]
    
    try:
        result = await vouchers_collection.insert_many(sample_vouchers)
        print(f"✅ Added {len(result.inserted_ids)} sample vouchers")
        
        # Verify insertion
        count = await vouchers_collection.count_documents({})
        print(f"📊 Total vouchers in database: {count}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to add sample vouchers: {e}")
        return False

async def test_voucher_api():
    """Test voucher API endpoint"""
    print("\n🧪 Testing Voucher API...")
    
    try:
        import httpx
        
        # Test health check first
        print("🔍 Testing health check...")
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                health_response = await client.get("http://localhost:3003/health")
                if health_response.status_code == 200:
                    print("✅ Voucher service is running")
                else:
                    print(f"❌ Voucher service health check failed: {health_response.status_code}")
                    return
            except Exception as e:
                print(f"❌ Voucher service not running: {e}")
                return
        
        # Test getAllVoucher endpoint
        print("🔍 Testing getAllVoucher endpoint...")
        async with httpx.AsyncClient(timeout=10.0) as client:
            api_response = await client.get("http://localhost:3003/api/vouchers/getAllVoucher")
            
            if api_response.status_code == 200:
                data = api_response.json()
                print("✅ API responded successfully")
                
                if data.get("success") and len(data.get("vouchers", [])) > 0:
                    vouchers = data['vouchers']
                    print(f"✅ Found {len(vouchers)} vouchers")
                    print("📄 Sample vouchers from API:")
                    for i, voucher in enumerate(vouchers[:3]):
                        title = voucher.get('title', 'No title')
                        category = voucher.get('category', 'No category')
                        price = voucher.get('price', 0)
                        print(f"  {i+1}. {title} | {category} | {price} VND")
                else:
                    print("⚠️ API responded but no vouchers returned")
                    print(f"📊 Full response: {data}")
            else:
                print(f"❌ API request failed: {api_response.status_code}")
                print(f"Response: {api_response.text}")
                
    except ImportError:
        print("⚠️ httpx not available, skipping API test")
        print("Install with: pip install httpx")
    except Exception as e:
        print(f"❌ API test failed: {e}")

async def update_database_config(best_endpoint):
    """Update database configuration in shared/database.py"""
    if not best_endpoint:
        return
    
    print(f"\n🔧 Updating database configuration...")
    print(f"Setting VOUCHER_DB_URI to: {best_endpoint['name']}")
    
    # Set environment variable for current session
    os.environ["VOUCHER_DB_URI"] = best_endpoint["uri"]
    print("✅ Environment variable updated for current session")
    
    print("📝 To make this permanent, add this to your .env file:")
    print(f"VOUCHER_DB_URI={best_endpoint['uri']}")

async def main():
    """Main debug function"""
    print("🐛 Voucher Service Debug Tool")
    print("Testing Multiple MongoDB Endpoints")
    print("=" * 60)
    
    # Find best endpoint
    best_endpoint = await find_best_endpoint()
    
    if not best_endpoint:
        print("❌ No working database endpoints found!")
        return
    
    # Update configuration
    await update_database_config(best_endpoint)
    
    # Connect to best endpoint and check if we need sample data
    print(f"\n🔗 Connecting to best endpoint: {best_endpoint['name']}")
    
    try:
        client = AsyncIOMotorClient(best_endpoint["uri"])
        await client.admin.command('ping')
        
        # Get database
        import urllib.parse
        parsed_uri = urllib.parse.urlparse(best_endpoint["uri"])
        if parsed_uri.path and len(parsed_uri.path) > 1:
            db_name = parsed_uri.path[1:]
            if '?' in db_name:
                db_name = db_name.split('?')[0]
        else:
            db_name = "voux_vouchers"
        
        db = client[db_name]
        vouchers_collection = db["vouchers"]
        
        # Check if we need sample data
        voucher_count = await vouchers_collection.count_documents({})
        
        if voucher_count == 0:
            print("\n📝 Database is empty, adding sample data...")
            await add_sample_vouchers(vouchers_collection)
        else:
            print(f"\n✅ Database already has {voucher_count} vouchers")
        
        # Close connection
        await client.close()
        
    except Exception as e:
        print(f"❌ Failed to connect to best endpoint: {e}")
        return
    
    # Test API
    await test_voucher_api()
    
    print("\n" + "=" * 60)
    print("🏁 Debug completed!")
    print("\n💡 Recommendations:")
    if best_endpoint:
        print(f"✅ Use endpoint: {best_endpoint['name']}")
        print(f"✅ Set VOUCHER_DB_URI={best_endpoint['uri']}")
    print("✅ Restart voucher service after updating configuration")

if __name__ == "__main__":
    asyncio.run(main()) 