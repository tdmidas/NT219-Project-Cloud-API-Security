#!/usr/bin/env python3
"""
Quick Start Testing Script for Voux Platform
This script combines voucher generation and API testing in one go
"""

import asyncio
import subprocess
import sys
import os
import time
from datetime import datetime

def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_step(step: str, description: str):
    """Print a formatted step"""
    print(f"\n🔸 Step {step}: {description}")
    print("-" * 40)

async def check_dependencies():
    """Check if required dependencies are installed"""
    print_step("1", "Checking dependencies")
    
    required_packages = [
        "motor",      # For MongoDB async operations
        "aiohttp",    # For HTTP testing
        "pymongo",    # For MongoDB operations
        "fastapi",    # For the API framework
        "uvicorn"     # For running the server
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("💡 Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All dependencies are installed!")
    return True

def check_mongodb_connection():
    """Check MongoDB connection"""
    print_step("2", "Checking MongoDB connection")
    
    try:
        import pymongo
        
        # Try local MongoDB first
        client = pymongo.MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=5000)
        client.server_info()
        print("✅ Local MongoDB is running (localhost:27017)")
        client.close()
        return "local"
        
    except Exception as e:
        print(f"❌ Local MongoDB not available: {e}")
        
        # Check for Atlas connection string in environment
        atlas_uri = os.getenv("VOUCHER_DB_URI")
        if atlas_uri and "mongodb+srv://" in atlas_uri:
            try:
                client = pymongo.MongoClient(atlas_uri, serverSelectionTimeoutMS=10000)
                client.server_info()
                print("✅ MongoDB Atlas connection available")
                client.close()
                return "atlas"
            except Exception as e:
                print(f"❌ MongoDB Atlas connection failed: {e}")
        
        print("❌ No MongoDB connection available")
        print("💡 Please start local MongoDB or set VOUCHER_DB_URI for Atlas")
        return None

def check_service_running(port: int, service_name: str):
    """Check if a service is running on a specific port"""
    import socket
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    
    try:
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"✅ {service_name} is running on port {port}")
            return True
        else:
            print(f"❌ {service_name} is not running on port {port}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking {service_name}: {e}")
        return False

async def generate_sample_vouchers(db_type: str):
    """Generate sample vouchers"""
    print_step("3", "Generating sample vouchers")
    
    try:
        # Import and run the voucher generator
        from motor.motor_asyncio import AsyncIOMotorClient
        import random
        from datetime import timedelta
        from bson import ObjectId
        
        # Database configuration
        if db_type == "local":
            db_uri = "mongodb://localhost:27017"
        else:
            db_uri = os.getenv("VOUCHER_DB_URI")
        
        print(f"🔗 Connecting to MongoDB ({db_type})...")
        client = AsyncIOMotorClient(db_uri)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
        
        # Use a simple voucher set for testing
        sample_vouchers = [
            {
                "title": "🍕 Pizza Palace - 30% Off",
                "description": "Giảm 30% cho tất cả pizza size L và XL",
                "voucher_type": "discount",
                "category": "food",
                "price": 50000,
                "discount_value": 30,
                "discount_type": "percentage",
                "quantity": 100,
                "terms_conditions": "Có hiệu lực trong 30 ngày",
                "image_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400",
                "expiry_date": datetime.utcnow() + timedelta(days=30),
                "owner_id": str(ObjectId()),
                "owner_username": "test_merchant",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
                "view_count": random.randint(10, 100),
                "purchase_count": random.randint(0, 20),
                "rating": round(random.uniform(4.0, 5.0), 1),
                "tags": ["pizza", "food", "restaurant"]
            },
            {
                "title": "☕ Coffee Bean - Buy 2 Get 1 Free",
                "description": "Mua 2 ly coffee được tặng 1 ly",
                "voucher_type": "gift",
                "category": "beverage",
                "price": 25000,
                "discount_value": 100,
                "discount_type": "percentage",
                "quantity": 50,
                "terms_conditions": "Áp dụng từ 8AM-5PM",
                "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400",
                "expiry_date": datetime.utcnow() + timedelta(days=14),
                "owner_id": str(ObjectId()),
                "owner_username": "coffee_shop",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
                "view_count": random.randint(10, 100),
                "purchase_count": random.randint(0, 20),
                "rating": round(random.uniform(4.0, 5.0), 1),
                "tags": ["coffee", "beverage", "cafe"]
            },
            {
                "title": "🛍️ Fashion Store - 500K Off",
                "description": "Giảm 500K cho đơn hàng từ 2M",
                "voucher_type": "discount",
                "category": "fashion",
                "price": 100000,
                "discount_value": 500000,
                "discount_type": "fixed",
                "quantity": 20,
                "terms_conditions": "Đơn hàng tối thiểu 2.000.000đ",
                "image_url": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400",
                "expiry_date": datetime.utcnow() + timedelta(days=45),
                "owner_id": str(ObjectId()),
                "owner_username": "fashion_store",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_active": True,
                "view_count": random.randint(10, 100),
                "purchase_count": random.randint(0, 20),
                "rating": round(random.uniform(4.0, 5.0), 1),
                "tags": ["fashion", "clothes", "shopping"]
            }
        ]
        
        # Insert vouchers
        db = client.voux_vouchers
        vouchers_collection = db.vouchers
        
        # Clear existing test vouchers
        await vouchers_collection.delete_many({"owner_username": {"$in": ["test_merchant", "coffee_shop", "fashion_store"]}})
        
        # Insert new vouchers
        result = await vouchers_collection.insert_many(sample_vouchers)
        
        print(f"✅ Successfully inserted {len(result.inserted_ids)} sample vouchers!")
        
        # Show summary
        for i, voucher in enumerate(sample_vouchers):
            print(f"   {i+1}. {voucher['title']} - {voucher['price']:,}đ")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate vouchers: {e}")
        return False

async def run_api_tests():
    """Run API tests"""
    print_step("4", "Running API tests")
    
    try:
        import aiohttp
        
        # Test configuration
        base_url = "http://localhost:3003"
        
        print(f"🧪 Testing API endpoints at {base_url}")
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            
            # Test 1: Health check
            print("Testing health check...")
            try:
                async with session.get(f"{base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Health check passed: {data.get('status', 'OK')}")
                    else:
                        print(f"❌ Health check failed: {response.status}")
                        return False
            except Exception as e:
                print(f"❌ Health check error: {e}")
                return False
            
            # Test 2: Get all vouchers
            print("Testing getAllVoucher...")
            try:
                async with session.get(f"{base_url}/api/vouchers/getAllVoucher?limit=5") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            vouchers = data.get("vouchers", [])
                            total = data.get("total", 0)
                            print(f"✅ getAllVoucher passed: {len(vouchers)} vouchers (Total: {total})")
                            
                            # Show sample vouchers
                            for i, voucher in enumerate(vouchers[:3]):
                                print(f"   {i+1}. {voucher.get('title', 'No title')} - {voucher.get('price', 0):,}đ")
                        else:
                            print(f"❌ getAllVoucher failed: {data.get('message', 'Unknown error')}")
                            return False
                    else:
                        print(f"❌ getAllVoucher failed: {response.status}")
                        return False
            except Exception as e:
                print(f"❌ getAllVoucher error: {e}")
                return False
            
            # Test 3: Get categories
            print("Testing categories...")
            try:
                async with session.get(f"{base_url}/api/vouchers/categories/") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            categories = data.get("categories", [])
                            print(f"✅ Categories passed: {len(categories)} categories found")
                            for cat in categories[:3]:
                                print(f"   • {cat.get('name', 'Unknown')}: {cat.get('count', 0)} vouchers")
                        else:
                            print(f"❌ Categories failed: {data.get('message', 'Unknown error')}")
                    else:
                        print(f"❌ Categories failed: {response.status}")
            except Exception as e:
                print(f"❌ Categories error: {e}")
            
            # Test 4: Search
            print("Testing search...")
            try:
                async with session.get(f"{base_url}/api/vouchers/search/?q=pizza&limit=3") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            vouchers = data.get("vouchers", [])
                            print(f"✅ Search passed: {len(vouchers)} results for 'pizza'")
                        else:
                            print(f"❌ Search failed: {data.get('message', 'Unknown error')}")
                    else:
                        print(f"❌ Search failed: {response.status}")
            except Exception as e:
                print(f"❌ Search error: {e}")
        
        print("✅ API tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ API testing failed: {e}")
        return False

async def main():
    """Main function"""
    print_header("🚀 Voux Platform - Quick Start Testing")
    
    print("This script will:")
    print("• Check dependencies")
    print("• Check MongoDB connection")
    print("• Generate sample vouchers")
    print("• Test API endpoints")
    print("\nPress Enter to continue or Ctrl+C to exit...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        return
    
    # Step 1: Check dependencies
    if not await check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        return
    
    # Step 2: Check MongoDB
    db_type = check_mongodb_connection()
    if not db_type:
        print("\n❌ MongoDB check failed. Please ensure MongoDB is running.")
        return
    
    # Step 3: Check if voucher service is running
    print_step("2.5", "Checking voucher service")
    if not check_service_running(3003, "Voucher Service"):
        print("\n⚠️ Voucher service is not running!")
        print("💡 Please start the service first:")
        print("   cd microservice-python")
        print("   python -m voucher_service.main")
        print("\nDo you want to continue with just data generation? (y/n): ", end="")
        
        try:
            choice = input().strip().lower()
            if choice != 'y':
                return
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            return
    
    # Step 4: Generate sample vouchers
    success = await generate_sample_vouchers(db_type)
    if not success:
        print("\n❌ Voucher generation failed.")
        return
    
    # Step 5: Run API tests (only if service is running)
    if check_service_running(3003, "Voucher Service"):
        success = await run_api_tests()
        if success:
            print_header("🎉 Quick Start Testing Completed Successfully!")
            print("\n✅ Summary:")
            print("• Dependencies: OK")
            print("• MongoDB: Connected")
            print("• Sample vouchers: Generated")
            print("• API tests: Passed")
            print("\n💡 Next steps:")
            print("• Start other services (auth, user, cart)")
            print("• Test with API Gateway")
            print("• Run comprehensive tests")
        else:
            print("\n⚠️ API tests failed, but data was generated successfully")
    else:
        print_header("📊 Data Generation Completed!")
        print("\n✅ Sample vouchers have been generated in the database")
        print("💡 Start the voucher service and run API tests:")
        print("   python test-voucher-api.py")

if __name__ == "__main__":
    asyncio.run(main()) 