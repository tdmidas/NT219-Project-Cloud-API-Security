#!/usr/bin/env python3
"""
Quick test for voucher API
"""

import asyncio
import httpx
import json

async def test_voucher_endpoints():
    """Test various voucher endpoints"""
    
    endpoints = [
        ("Direct Voucher Service", "http://localhost:3003/api/vouchers/getAllVoucher"),
        ("Via API Gateway", "http://localhost:8060/api/vouchers/getAllVoucher"),
    ]
    
    print("🧪 Testing Voucher API Endpoints")
    print("=" * 50)
    
    for name, url in endpoints:
        print(f"\n📍 Testing {name}")
        print(f"   URL: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   ✅ JSON Response received")
                        print(f"   Response keys: {list(data.keys())}")
                        print(f"   Success: {data.get('success', 'Not found')}")
                        
                        if 'data' in data:
                            print(f"   Data type: {type(data['data'])}")
                            if isinstance(data['data'], list):
                                print(f"   Data length: {len(data['data'])}")
                                if len(data['data']) > 0:
                                    first_item = data['data'][0]
                                    print(f"   First item keys: {list(first_item.keys())}")
                                    print(f"   Sample title: {first_item.get('title', 'N/A')}")
                                else:
                                    print("   ⚠️ Data array is empty")
                            else:
                                print(f"   ❌ Data is not a list: {data['data']}")
                        else:
                            print("   ❌ No 'data' key in response")
                            
                        # Show first 300 chars of response
                        response_str = json.dumps(data, indent=2)
                        if len(response_str) > 300:
                            print(f"   Response preview: {response_str[:300]}...")
                        else:
                            print(f"   Full response: {response_str}")
                            
                    except json.JSONDecodeError as e:
                        print(f"   ❌ Invalid JSON: {e}")
                        print(f"   Raw response: {response.text[:200]}...")
                        
                else:
                    print(f"   ❌ HTTP Error: {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
                    
        except httpx.ConnectError:
            print(f"   ❌ Connection failed - service not running")
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def test_service_health():
    """Test service health endpoints"""
    
    services = [
        ("Voucher Service", "http://localhost:3003/health"),
        ("API Gateway", "http://localhost:8060/health"),
    ]
    
    print("\n🏥 Health Check")
    print("=" * 30)
    
    for name, url in services:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    print(f"✅ {name}: Running")
                else:
                    print(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Not running ({e})")

async def main():
    await test_service_health()
    await test_voucher_endpoints()
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print("- Check if services are running")
    print("- Verify API response format")
    print("- Ensure frontend can parse the response")

if __name__ == "__main__":
    asyncio.run(main()) 