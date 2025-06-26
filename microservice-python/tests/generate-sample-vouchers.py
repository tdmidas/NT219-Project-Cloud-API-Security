#!/usr/bin/env python3
"""
Generate Sample Vouchers for Voux Platform
This script creates sample vouchers and inserts them into MongoDB
"""

import asyncio
import os
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import random

# Sample voucher data
SAMPLE_VOUCHERS = [
    {
        "title": "🍕 Pizza Palace - 30% Off",
        "description": "Giảm 30% cho tất cả pizza size L và XL. Áp dụng cho dine-in và takeaway.",
        "voucher_type": "discount",
        "category": "food",
        "price": 50000,
        "discount_value": 30,
        "discount_type": "percentage",
        "quantity": 100,
        "terms_conditions": "Không áp dụng cùng với khuyến mãi khác. Có hiệu lực trong 30 ngày.",
        "image_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400",
        "expiry_date": datetime.utcnow() + timedelta(days=30)
    },
    {
        "title": "☕ Coffee Bean - Buy 2 Get 1 Free",
        "description": "Mua 2 ly coffee bất kỳ, được tặng 1 ly coffee cùng loại hoặc nhỏ hơn.",
        "voucher_type": "gift",
        "category": "beverage",
        "price": 25000,
        "discount_value": 100,
        "discount_type": "percentage",
        "quantity": 50,
        "terms_conditions": "Áp dụng từ 8AM-5PM. Không áp dụng cho weekend.",
        "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=400",
        "expiry_date": datetime.utcnow() + timedelta(days=14)
    },
    {
        "title": "🛍️ Fashion Store - 500K Off",
        "description": "Giảm 500.000đ cho đơn hàng từ 2.000.000đ trở lên. Áp dụng toàn bộ sản phẩm.",
        "voucher_type": "discount",
        "category": "fashion",
        "price": 100000,
        "discount_value": 500000,
        "discount_type": "fixed",
        "quantity": 20,
        "terms_conditions": "Đơn hàng tối thiểu 2.000.000đ. Không áp dụng cho sản phẩm sale.",
        "image_url": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400",
        "expiry_date": datetime.utcnow() + timedelta(days=45)
    },
    {
        "title": "🎬 Cinema Tickets - 2 for 1",
        "description": "Mua 1 vé xem phim, được tặng 1 vé miễn phí. Áp dụng cho tất cả suất chiếu.",
        "voucher_type": "gift",
        "category": "entertainment",
        "price": 80000,
        "discount_value": 50,
        "discount_type": "percentage",
        "quantity": 75,
        "terms_conditions": "Không áp dụng cho phim 3D và IMAX. Book trước 24h.",
        "image_url": "https://images.unsplash.com/photo-1489185078342-8d41b32a8d3b?w=400",
        "expiry_date": datetime.utcnow() + timedelta(days=60)
    },
    {
        "title": "🏥 Healthcare Check-up Package",
        "description": "Gói khám sức khỏe tổng quát với giá ưu đãi. Bao gồm xét nghiệm cơ bản.",
        "voucher_type": "discount",
        "category": "healthcare",
        "price": 200000,
        "discount_value": 40,
        "discount_type": "percentage",
        "quantity": 30,
        "terms_conditions": "Đặt lịch trước 48h. Có hiệu lực trong 3 tháng.",
        "image_url": "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?w=400",
        "expiry_date": datetime.utcnow() + timedelta(days=90)
    },
    {
        "title": "🚗 Car Wash Premium Service",
        "description": "Dịch vụ rửa xe cao cấp với công nghệ không chạm. Bao gồm wax và làm sạch nội thất.",
        "voucher_type": "discount",
        "category": "automotive",
        "price": 75000,
        "discount_value": 25,
        "discount_type": "percentage",
        "quantity": 40,
        "terms_conditions": "Áp dụng cho xe 4-7 chỗ. Không áp dụng ngày lễ.",
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400",
        "expiry_date": datetime.utcnow() + timedelta(days=21)
    },
    {
        "title": "🎓 Online Course - Programming Bootcamp",
        "description": "Khóa học lập trình full-stack 6 tháng với mentor 1-1. Cam kết có việc làm.",
        "voucher_type": "discount",
        "category": "education",
        "price": 500000,
        "discount_value": 1500000,
        "discount_type": "fixed",
        "quantity": 15,
        "terms_conditions": "Yêu cầu cam kết học tập 40h/tuần. Có test đầu vào.",
        "image_url": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=400",
        "expiry_date": datetime.utcnow() + timedelta(days=180)
    },
    {
        "title": "🏋️ Gym Membership - 3 Months",
        "description": "Gói tập gym 3 tháng với PT cá nhân 2 buổi/tuần. Bao gồm sauna và massage.",
        "voucher_type": "discount",
        "category": "fitness",
        "price": 300000,
        "discount_value": 35,
        "discount_type": "percentage",
        "quantity": 25,
        "terms_conditions": "Khám sức khỏe trước khi tập. Không hoàn tiền.",
        "image_url": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=400",
        "expiry_date": datetime.utcnow() + timedelta(days=120)
    },
    {
        "title": "✈️ Travel Package - Da Nang 3N2D",
        "description": "Tour Đà Nẵng 3 ngày 2 đêm. Bao gồm vé máy bay, khách sạn 4 sao, và tour city.",
        "voucher_type": "discount",
        "category": "travel",
        "price": 800000,
        "discount_value": 1000000,
        "discount_type": "fixed",
        "quantity": 10,
        "terms_conditions": "Book trước 30 ngày. Không áp dụng lễ tết.",
        "image_url": "https://images.unsplash.com/photo-1559592413-7cec4d0d2d94?w=400",
        "expiry_date": datetime.utcnow() + timedelta(days=365)
    },
    {
        "title": "📱 iPhone 15 Pro - Cashback 10%",
        "description": "Mua iPhone 15 Pro được hoàn tiền 10% qua ví điện tử. Bảo hành chính hãng 12 tháng.",
        "voucher_type": "cashback",
        "category": "technology",
        "price": 200000,
        "discount_value": 10,
        "discount_type": "percentage",
        "quantity": 5,
        "terms_conditions": "Hoàn tiền trong 30 ngày. Máy chính hãng VN/A.",
        "image_url": "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=400",
        "expiry_date": datetime.utcnow() + timedelta(days=14)
    }
]

# Sample users for voucher ownership
SAMPLE_USERS = [
    {
        "_id": ObjectId(),
        "username": "voucher_admin",
        "email": "admin@voux.com"
    },
    {
        "_id": ObjectId(), 
        "username": "merchant_food",
        "email": "food@voux.com"
    },
    {
        "_id": ObjectId(),
        "username": "merchant_tech", 
        "email": "tech@voux.com"
    }
]

async def connect_to_database(db_uri: str):
    """Connect to MongoDB"""
    try:
        client = AsyncIOMotorClient(db_uri)
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return None

async def insert_sample_vouchers(client, database_name: str = "voux_vouchers"):
    """Insert sample vouchers into database"""
    try:
        db = client[database_name]
        vouchers_collection = db.vouchers
        
        # Clear existing sample vouchers (optional)
        delete_result = await vouchers_collection.delete_many({"title": {"$regex": "🍕|☕|🛍️|🎬|🏥|🚗|🎓|🏋️|✈️|📱"}})
        print(f"🗑️ Deleted {delete_result.deleted_count} existing sample vouchers")
        
        # Prepare vouchers with random owners
        vouchers_to_insert = []
        
        for i, voucher_data in enumerate(SAMPLE_VOUCHERS):
            # Assign random owner
            owner = random.choice(SAMPLE_USERS)
            
            voucher = {
                **voucher_data,
                "owner_id": str(owner["_id"]),
                "owner_username": owner["username"],
                "created_at": datetime.utcnow() - timedelta(days=random.randint(0, 30)),
                "updated_at": datetime.utcnow(),
                "is_active": True,
                "view_count": random.randint(10, 500),
                "purchase_count": random.randint(0, 50),
                "rating": round(random.uniform(3.5, 5.0), 1),
                "tags": []
            }
            
            # Add category-specific tags
            if voucher["category"] == "food":
                voucher["tags"] = ["pizza", "restaurant", "dine-in", "takeaway"]
            elif voucher["category"] == "beverage":
                voucher["tags"] = ["coffee", "drink", "cafe", "morning"]
            elif voucher["category"] == "fashion":
                voucher["tags"] = ["clothes", "shopping", "style", "discount"]
            elif voucher["category"] == "entertainment":
                voucher["tags"] = ["movie", "cinema", "film", "tickets"]
            elif voucher["category"] == "healthcare":
                voucher["tags"] = ["health", "checkup", "medical", "wellness"]
            elif voucher["category"] == "automotive":
                voucher["tags"] = ["car", "wash", "auto", "service"]
            elif voucher["category"] == "education":
                voucher["tags"] = ["learning", "course", "programming", "bootcamp"]
            elif voucher["category"] == "fitness":
                voucher["tags"] = ["gym", "workout", "fitness", "health"]
            elif voucher["category"] == "travel":
                voucher["tags"] = ["tour", "vacation", "danang", "travel"]
            elif voucher["category"] == "technology":
                voucher["tags"] = ["iphone", "apple", "smartphone", "tech"]
            
            vouchers_to_insert.append(voucher)
        
        # Insert vouchers
        result = await vouchers_collection.insert_many(vouchers_to_insert)
        print(f"✅ Successfully inserted {len(result.inserted_ids)} sample vouchers!")
        
        # Print summary
        print("\n📊 Sample Vouchers Summary:")
        for i, voucher in enumerate(vouchers_to_insert):
            print(f"  {i+1}. {voucher['title']} - {voucher['price']:,}đ ({voucher['category']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to insert vouchers: {e}")
        return False

async def verify_vouchers(client, database_name: str = "voux_vouchers"):
    """Verify inserted vouchers"""
    try:
        db = client[database_name]
        vouchers_collection = db.vouchers
        
        # Count total vouchers
        total_count = await vouchers_collection.count_documents({})
        print(f"\n📈 Total vouchers in database: {total_count}")
        
        # Count by category
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        category_counts = await vouchers_collection.aggregate(pipeline).to_list(length=None)
        
        print("\n📊 Vouchers by Category:")
        for item in category_counts:
            print(f"  {item['_id']}: {item['count']} vouchers")
        
        # Show sample vouchers
        print("\n📋 Sample Vouchers (First 3):")
        sample_vouchers = await vouchers_collection.find({}).limit(3).to_list(length=3)
        
        for voucher in sample_vouchers:
            print(f"  • {voucher['title']}")
            print(f"    Category: {voucher['category']}")
            print(f"    Price: {voucher['price']:,}đ")
            print(f"    Quantity: {voucher['quantity']}")
            print(f"    Expires: {voucher['expiry_date'].strftime('%Y-%m-%d')}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to verify vouchers: {e}")
        return False

async def main():
    """Main function"""
    print("🎫 Voux Platform - Sample Voucher Generator")
    print("=" * 50)
    
    # Database configuration
    db_uris = {
        "local": "mongodb://localhost:27017",
        "atlas": os.getenv("VOUCHER_DB_URI", "mongodb+srv://minhdai:mutoyugi@cluster0.xqhnrnv.mongodb.net/voux_voucher?retryWrites=true&w=majority&appName=Cluster0")
    }
    
    # Choose database
    print("Select database to populate:")
    print("1. Local MongoDB (localhost:27017)")
    print("2. MongoDB Atlas (from environment variable)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        db_uri = db_uris["local"]
        db_name = "voux_vouchers"
        print(f"🔗 Using local MongoDB: {db_uri}")
    elif choice == "2":
        db_uri = db_uris["atlas"]
        db_name = "voux_vouchers"
        print(f"🔗 Using MongoDB Atlas")
    else:
        print("❌ Invalid choice")
        return
    
    # Connect to database
    client = await connect_to_database(db_uri)
    if not client:
        return
    
    try:
        # Insert sample vouchers
        success = await insert_sample_vouchers(client, db_name)
        if not success:
            return
        
        # Verify insertion
        await verify_vouchers(client, db_name)
        
        print("\n🎉 Sample voucher generation completed successfully!")
        print("\n💡 Next steps:")
        print("1. Start the voucher service")
        print("2. Test the /getAllVoucher endpoint")
        print("3. Use the test script: python test-voucher-api.py")
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main()) 