#!/usr/bin/env python3
"""
Test Voucher API Endpoints
This script tests various voucher endpoints including getAllVoucher
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# API Configuration
API_CONFIGS = {
    "local": {
        "base_url": "http://localhost:3003",
        "api_gateway": "http://localhost:8060"
    },
    "production": {
        "base_url": "https://api.voux-platform.shop",
        "api_gateway": "https://api.voux-platform.shop"
    }
}

class VoucherAPITester:
    """Test class for Voucher API endpoints"""
    
    def __init__(self, base_url: str, use_gateway: bool = False):
        self.base_url = base_url
        self.use_gateway = use_gateway
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "Voux-API-Tester/1.0",
                "Content-Type": "application/json"
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def get_endpoint_url(self, endpoint: str) -> str:
        """Get full URL for endpoint"""
        if self.use_gateway:
            return f"{self.base_url}/api/vouchers{endpoint}"
        else:
            return f"{self.base_url}/api/vouchers{endpoint}"
    
    async def test_health_check(self):
        """Test service health"""
        print("🏥 Testing health check...")
        
        try:
            if self.use_gateway:
                url = f"{self.base_url}/health"
            else:
                url = f"{self.base_url}/health"
                
            start_time = time.time()
            async with self.session.get(url) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed ({response_time:.3f}s)")
                    print(f"   Status: {data.get('status', 'Unknown')}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_get_all_vouchers(self, skip: int = 0, limit: int = 10, category: str = None):
        """Test getAllVoucher endpoint"""
        print(f"\n🎫 Testing getAllVoucher (skip={skip}, limit={limit}, category={category})...")
        
        try:
            # Build URL with parameters
            url = self.get_endpoint_url("/getAllVoucher")
            params = {
                "skip": skip,
                "limit": limit
            }
            
            if category:
                params["category"] = category
            
            start_time = time.time()
            async with self.session.get(url) as response:
                response_time = time.time() - start_time
                data = await response.json()
                
                if response.status == 200:
                    print(f"✅ getAllVoucher successful ({response_time:.3f}s)")
                    
                    if data.get("success"):
                        vouchers = data.get("vouchers", [])
                        total = data.get("total", 0)
                        
                        print(f"   📊 Results: {len(vouchers)} vouchers (Total: {total})")
                        
                        # Show sample vouchers
                        for i, voucher in enumerate(vouchers[:3]):
                            print(f"   {i+1}. {voucher.get('title', 'No title')}")
                            print(f"      Category: {voucher.get('category', 'N/A')}")
                            print(f"      Price: {voucher.get('price', 0):,}đ")
                            print(f"      Quantity: {voucher.get('quantity', 0)}")
                            
                        if len(vouchers) > 3:
                            print(f"   ... and {len(vouchers) - 3} more vouchers")
                            
                        return vouchers
                    else:
                        print(f"❌ API returned success=false: {data.get('message', 'Unknown error')}")
                        return []
                else:
                    print(f"❌ getAllVoucher failed: {response.status}")
                    print(f"   Response: {data}")
                    return []
                    
        except Exception as e:
            print(f"❌ getAllVoucher error: {e}")
            return []
    
    async def test_get_categories(self):
        """Test getCategories endpoint"""
        print("\n📂 Testing getCategories...")
        
        try:
            url = self.get_endpoint_url("/categories/")
            
            start_time = time.time()
            async with self.session.get(url) as response:
                response_time = time.time() - start_time
                data = await response.json()
                
                if response.status == 200:
                    print(f"✅ getCategories successful ({response_time:.3f}s)")
                    
                    if data.get("success"):
                        categories = data.get("categories", [])
                        print(f"   📂 Categories found: {len(categories)}")
                        
                        for category in categories:
                            print(f"   • {category.get('name', 'Unknown')} ({category.get('count', 0)} vouchers)")
                            
                        return categories
                    else:
                        print(f"❌ Categories API returned success=false")
                        return []
                else:
                    print(f"❌ getCategories failed: {response.status}")
                    return []
                    
        except Exception as e:
            print(f"❌ getCategories error: {e}")
            return []
    
    async def test_search_vouchers(self, query: str = "pizza", limit: int = 5):
        """Test search vouchers endpoint"""
        print(f"\n🔍 Testing search vouchers (query='{query}', limit={limit})...")
        
        try:
            url = self.get_endpoint_url("/search/")
            params = {
                "q": query,
                "limit": limit
            }
            
            start_time = time.time()
            async with self.session.get(url, params=params) as response:
                response_time = time.time() - start_time
                data = await response.json()
                
                if response.status == 200:
                    print(f"✅ Search successful ({response_time:.3f}s)")
                    
                    if data.get("success"):
                        vouchers = data.get("vouchers", [])
                        print(f"   🔍 Search results: {len(vouchers)} vouchers")
                        
                        for i, voucher in enumerate(vouchers):
                            print(f"   {i+1}. {voucher.get('title', 'No title')}")
                            print(f"      Match score: {voucher.get('score', 'N/A')}")
                            
                        return vouchers
                    else:
                        print(f"❌ Search API returned success=false")
                        return []
                else:
                    print(f"❌ Search failed: {response.status}")
                    return []
                    
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    async def test_get_voucher_by_id(self, voucher_id: str):
        """Test get voucher by ID endpoint"""
        print(f"\n📄 Testing get voucher by ID ({voucher_id[:8]}...)...")
        
        try:
            url = self.get_endpoint_url(f"/{voucher_id}")
            
            start_time = time.time()
            async with self.session.get(url) as response:
                response_time = time.time() - start_time
                data = await response.json()
                
                if response.status == 200:
                    print(f"✅ Get voucher by ID successful ({response_time:.3f}s)")
                    
                    if data.get("success"):
                        voucher = data.get("voucher", {})
                        print(f"   📄 Voucher: {voucher.get('title', 'No title')}")
                        print(f"   📊 Views: {voucher.get('view_count', 0)}")
                        print(f"   ⭐ Rating: {voucher.get('rating', 'N/A')}")
                        
                        return voucher
                    else:
                        print(f"❌ Get voucher API returned success=false")
                        return {}
                else:
                    print(f"❌ Get voucher by ID failed: {response.status}")
                    return {}
                    
        except Exception as e:
            print(f"❌ Get voucher by ID error: {e}")
            return {}
    
    async def test_get_valid_vouchers(self):
        """Test getValidVouchers endpoint"""
        print("\n✅ Testing getValidVouchers...")
        
        try:
            url = self.get_endpoint_url("/getValidVouchers")
            
            start_time = time.time()
            async with self.session.get(url) as response:
                response_time = time.time() - start_time
                data = await response.json()
                
                if response.status == 200:
                    print(f"✅ getValidVouchers successful ({response_time:.3f}s)")
                    
                    if data.get("success"):
                        vouchers = data.get("vouchers", [])
                        print(f"   ✅ Valid vouchers: {len(vouchers)}")
                        
                        return vouchers
                    else:
                        print(f"❌ Valid vouchers API returned success=false")
                        return []
                else:
                    print(f"❌ getValidVouchers failed: {response.status}")
                    return []
                    
        except Exception as e:
            print(f"❌ getValidVouchers error: {e}")
            return []

async def run_comprehensive_test(api_config: dict, use_gateway: bool = False):
    """Run comprehensive API tests"""
    
    base_url = api_config["api_gateway"] if use_gateway else api_config["base_url"]
    
    print(f"\n🚀 Starting comprehensive voucher API tests")
    print(f"📍 Base URL: {base_url}")
    print(f"🌐 Using Gateway: {use_gateway}")
    print("=" * 70)
    
    async with VoucherAPITester(base_url, use_gateway) as tester:
        
        # Test 1: Health check
        health_ok = await tester.test_health_check()
        if not health_ok:
            print("❌ Health check failed. Service may not be running.")
            return
        
        # Test 2: Get all vouchers (default)
        all_vouchers = await tester.test_get_all_vouchers()
        
        # Test 3: Get all vouchers with pagination
        await tester.test_get_all_vouchers(skip=5, limit=3)
        
        # Test 4: Get categories
        categories = await tester.test_get_categories()
        
        # Test 5: Filter by category
        if categories:
            category_name = categories[0].get("name", "food")
            await tester.test_get_all_vouchers(limit=5, category=category_name)
        
        # Test 6: Search vouchers
        await tester.test_search_vouchers("pizza")
        await tester.test_search_vouchers("coffee", limit=3)
        
        # Test 7: Get valid vouchers
        valid_vouchers = await tester.test_get_valid_vouchers()
        
        # Test 8: Get voucher by ID
        if all_vouchers:
            voucher_id = all_vouchers[0].get("_id")
            if voucher_id:
                await tester.test_get_voucher_by_id(voucher_id)
        
        print("\n" + "=" * 70)
        print("🎉 Comprehensive testing completed!")

async def main():
    """Main function"""
    print("🧪 Voux Platform - Voucher API Tester")
    print("=" * 50)
    
    # Environment selection
    print("Select testing environment:")
    print("1. Local Development (localhost)")
    print("2. Production/Staging")
    
    env_choice = input("Enter choice (1 or 2): ").strip()
    
    if env_choice == "1":
        api_config = API_CONFIGS["local"]
        print("🔧 Using local development environment")
    elif env_choice == "2":
        api_config = API_CONFIGS["production"]
        print("🌐 Using production environment")
    else:
        print("❌ Invalid choice")
        return
    
    # Gateway selection
    print("\nSelect API access method:")
    print("1. Direct service (port 3003)")
    print("2. Via API Gateway (port 8000)")
    
    gateway_choice = input("Enter choice (1 or 2): ").strip()
    
    use_gateway = gateway_choice == "2"
    
    try:
        await run_comprehensive_test(api_config, use_gateway)
        
        print("\n💡 Testing completed! Key observations:")
        print("• Check if all endpoints return expected data")
        print("• Verify response times are acceptable")
        print("• Ensure pagination works correctly")
        print("• Confirm search functionality")
        print("• Validate voucher data structure")
        
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 