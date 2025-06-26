#!/usr/bin/env python3
"""
Test script for Cart Service API
Tests cart endpoints matching JS backend
"""

import asyncio
import httpx
import json
from typing import Dict, Any, Optional

class CartAPITester:
    """Test cart service API endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:3004", gateway_url: str = "http://localhost:8060"):
        self.base_url = base_url
        self.gateway_url = gateway_url
        self.access_token: Optional[str] = None
        self.test_voucher_id: Optional[str] = None
    
    def print_header(self, title: str):
        """Print test section header"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print('='*60)
    
    def print_step(self, step: str):
        """Print test step"""
        print(f"\n📍 {step}")
    
    async def check_services_health(self):
        """Check if required services are running"""
        self.print_header("Health Check")
        
        services = [
            ("Cart Service", f"{self.base_url}/health"),
            ("API Gateway", f"{self.gateway_url}/health"),
            ("Auth Service", "http://localhost:3001/health"),
            ("Voucher Service", "http://localhost:3003/health")
        ]
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for name, url in services:
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        print(f"✅ {name}: Running")
                    else:
                        print(f"❌ {name}: HTTP {response.status_code}")
                        return False
                except Exception as e:
                    print(f"❌ {name}: Not running ({e})")
                    return False
        
        return True
    
    async def login_test_user(self):
        """Login to get access token"""
        self.print_step("Logging in test user...")
        
        login_data = {
            "username": "minhdai1234",
            "password": "Minhdai100504@",
            "remember_me": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Try to login via API Gateway
                response = await client.post(f"{self.gateway_url}/api/auth/login", json=login_data)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("access_token"):
                        self.access_token = data["access_token"]
                        print(f"✅ Login successful")
                        print(f"   User: {data.get('user', {}).get('username', 'Unknown')}")
                        print(f"   Token: {self.access_token[:20]}...")
                        return True
                    else:
                        print(f"❌ Login failed: {data.get('message', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ Login failed: HTTP {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Login error: {e}")
                return False
    
    async def get_test_voucher_id(self):
        """Get a test voucher ID"""
        self.print_step("Getting test voucher ID...")
        
        async with httpx.AsyncClient() as client:
            try:
                # Get vouchers from voucher service
                response = await client.get("http://localhost:3003/api/vouchers/getAllVoucher")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("data"):
                        vouchers = data["data"]
                        if vouchers:
                            self.test_voucher_id = vouchers[0].get("id") or vouchers[0].get("_id")
                            print(f"✅ Found test voucher: {self.test_voucher_id}")
                            print(f"   Title: {vouchers[0].get('title', 'Unknown')}")
                            return True
                
                print("❌ No vouchers found")
                return False
                
            except Exception as e:
                print(f"❌ Error getting vouchers: {e}")
                return False
    
    async def test_get_cart_empty(self):
        """Test getting empty cart"""
        self.print_step("Testing GET /api/cart/ (empty cart)")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                # Test via API Gateway
                response = await client.get(f"{self.gateway_url}/api/cart/", headers=headers)
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Response: {json.dumps(data, indent=2)}")
                    
                    # Verify empty cart structure
                    if data.get("success") and "cart" in data:
                        cart = data["cart"]
                        vouchers = cart.get("vouchers", [])
                        print(f"✅ Cart has {len(vouchers)} items (expected: 0)")
                        return True
                    else:
                        print("❌ Invalid response structure")
                        return False
                else:
                    print(f"❌ Failed: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                return False
    
    async def test_add_to_cart(self):
        """Test adding item to cart"""
        self.print_step("Testing POST /api/cart/add")
        
        if not self.test_voucher_id:
            print("❌ No test voucher ID available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Request body matching JS backend
        request_body = {
            "voucherId": self.test_voucher_id
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.gateway_url}/api/cart/add", 
                    headers=headers,
                    json=request_body
                )
                
                print(f"Status: {response.status_code}")
                print(f"Request body: {json.dumps(request_body, indent=2)}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Response: {json.dumps(data, indent=2)}")
                    
                    if data.get("success"):
                        print("✅ Successfully added to cart")
                        return True
                    else:
                        print(f"❌ Failed: {data.get('message', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ Failed: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                return False
    
    async def test_get_cart_with_items(self):
        """Test getting cart with items"""
        self.print_step("Testing GET /api/cart/ (with items)")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.gateway_url}/api/cart/", headers=headers)
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Response: {json.dumps(data, indent=2)}")
                    
                    # Verify cart has items
                    if data.get("success") and "cart" in data:
                        cart = data["cart"]
                        vouchers = cart.get("vouchers", [])
                        print(f"✅ Cart has {len(vouchers)} items")
                        
                        if vouchers:
                            first_item = vouchers[0]
                            voucher_info = first_item.get("voucherId", {})
                            print(f"   First item: {voucher_info.get('title', 'Unknown')}")
                            print(f"   Quantity: {first_item.get('quantity', 0)}")
                        
                        return True
                    else:
                        print("❌ Invalid response structure")
                        return False
                else:
                    print(f"❌ Failed: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                return False
    
    async def test_cart_summary(self):
        """Test cart summary endpoint"""
        self.print_step("Testing GET /api/cart/summary")
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.gateway_url}/api/cart/summary", headers=headers)
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Response: {json.dumps(data, indent=2)}")
                    
                    if data.get("success") and "summary" in data:
                        summary = data["summary"]
                        print(f"✅ Summary - Items: {summary.get('total_items', 0)}, Quantity: {summary.get('total_quantity', 0)}, Amount: {summary.get('total_amount', 0)}")
                        return True
                    else:
                        print("❌ Invalid response structure")
                        return False
                else:
                    print(f"❌ Failed: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                return False
    
    async def test_remove_from_cart(self):
        """Test removing item from cart"""
        self.print_step("Testing POST /api/cart/remove")
        
        if not self.test_voucher_id:
            print("❌ No test voucher ID available")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Request body matching JS backend
        request_body = {
            "voucherId": self.test_voucher_id
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.gateway_url}/api/cart/remove", 
                    headers=headers,
                    json=request_body
                )
                
                print(f"Status: {response.status_code}")
                print(f"Request body: {json.dumps(request_body, indent=2)}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Response: {json.dumps(data, indent=2)}")
                    
                    if data.get("success"):
                        print("✅ Successfully removed from cart")
                        return True
                    else:
                        print(f"❌ Failed: {data.get('message', 'Unknown error')}")
                        return False
                else:
                    print(f"❌ Failed: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                return False
    
    async def test_cart_direct_endpoint(self):
        """Test direct cart service endpoint (without auth for health check)"""
        self.print_step("Testing direct cart service endpoint")
        
        async with httpx.AsyncClient() as client:
            try:
                # Test health endpoint
                response = await client.get(f"{self.base_url}/health")
                
                print(f"Health Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Cart Service Health: {json.dumps(data, indent=2)}")
                    return True
                else:
                    print(f"❌ Cart service not healthy: {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error connecting to cart service: {e}")
                return False

async def main():
    """Main test function"""
    print("🧪 Cart Service API Testing")
    print("Testing endpoints matching JS backend")
    
    tester = CartAPITester()
    
    # Step 1: Check services
    if not await tester.check_services_health():
        print("\n❌ Some services are not running. Please start all services first.")
        return
    
    # Step 2: Login
    if not await tester.login_test_user():
        print("\n❌ Login failed. Please check auth service and user credentials.")
        return
    
    # Step 3: Get test voucher
    if not await tester.get_test_voucher_id():
        print("\n❌ No test vouchers available. Please run voucher generation script first.")
        return
    
    # Step 4: Test cart endpoints
    tests = [
        ("Test direct cart service", tester.test_cart_direct_endpoint),
        ("Test empty cart", tester.test_get_cart_empty),
        ("Test add to cart", tester.test_add_to_cart),
        ("Test cart with items", tester.test_get_cart_with_items),
        ("Test cart summary", tester.test_cart_summary),
        ("Test remove from cart", tester.test_remove_from_cart),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Results Summary")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Total: {passed + failed} tests")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Cart API is working correctly.")
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the errors above.")

if __name__ == "__main__":
    asyncio.run(main()) 