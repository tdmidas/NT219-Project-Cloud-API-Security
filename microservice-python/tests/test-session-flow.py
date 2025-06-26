#!/usr/bin/env python3
"""
Test Session Flow - Register, Login, Refresh
"""

import asyncio
import httpx
import json
import time

async def test_complete_session_flow():
    """Test complete session flow"""
    print("🔄 Testing Complete Session Flow")
    print("=" * 50)
    
    base_url = "http://localhost:8060"  # API Gateway
    
    # Step 1: Register new user
    print("\n📍 Step 1: Register new user...")
    username = f"sessiontest{int(time.time())}"  # Unique username
    
    register_data = {
        "username": username,
        "email": f"{username}@example.com",
        "password": "securepass123"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{base_url}/api/auth/register", json=register_data)
            if response.status_code == 200:
                print(f"✅ Registration successful for {username}")
            else:
                print(f"❌ Registration failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    # Step 2: Login
    print("\n📍 Step 2: Login...")
    login_data = {
        "username": username,
        "password": "securepass123",
        "remember_me": False
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{base_url}/api/auth/login", json=login_data)
            if response.status_code == 200:
                data = response.json()
                print("✅ Login successful")
                
                # Print session info
                print(f"   Access Token: {data.get('access_token', 'N/A')[:20]}...")
                print(f"   Expires in: {data.get('expires_in', 'N/A')} seconds")
                print(f"   RBAC Role: {data.get('rbac', {}).get('role', 'N/A')}")
                
                permissions = data.get('rbac', {}).get('permissions', [])
                cart_perms = [p for p in permissions if 'cart' in p]
                print(f"   Cart Permissions: {cart_perms}")
                
                access_token = data.get("access_token")
                cookies = response.cookies
                
            else:
                print(f"❌ Login failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    # Step 3: Test protected endpoint (cart)
    print("\n📍 Step 3: Test cart access...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient(cookies=cookies) as client:
        try:
            response = await client.get(f"{base_url}/api/cart/", headers=headers)
            if response.status_code == 200:
                print("✅ Cart access successful")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Cart access failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Cart access error: {e}")
    
    # Step 4: Wait for token to expire and test refresh
    print("\n📍 Step 4: Wait for token expiry and test refresh...")
    print("   Waiting 50 seconds for token to expire...")
    
    # Wait longer than token expiry (45 seconds)
    await asyncio.sleep(50)
    
    # Try to access cart again (should fail)
    print("   Testing expired token...")
    async with httpx.AsyncClient(cookies=cookies) as client:
        try:
            response = await client.get(f"{base_url}/api/cart/", headers=headers)
            if response.status_code == 401:
                print("✅ Expired token correctly rejected")
            else:
                print(f"⚠️ Unexpected response: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing expired token: {e}")
    
    # Step 5: Test refresh token
    print("\n📍 Step 5: Test refresh token...")
    
    async with httpx.AsyncClient(cookies=cookies) as client:
        try:
            response = await client.post(f"{base_url}/api/auth/refresh", json={})
            print(f"   Refresh response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Token refresh successful")
                print(f"   New access token: {data.get('access_token', 'N/A')[:20]}...")
                print(f"   New expires in: {data.get('expires_in', 'N/A')} seconds")
                
                # Test cart with new token
                new_token = data.get("access_token")
                new_headers = {"Authorization": f"Bearer {new_token}"}
                
                cart_response = await client.get(f"{base_url}/api/cart/", headers=new_headers)
                if cart_response.status_code == 200:
                    print("✅ Cart access with new token successful")
                else:
                    print(f"❌ Cart access with new token failed: {cart_response.status_code}")
                    
            else:
                print(f"❌ Token refresh failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Refresh error: {e}")
    
    # Step 6: Test logout
    print("\n📍 Step 6: Test logout...")
    
    async with httpx.AsyncClient(cookies=cookies) as client:
        try:
            response = await client.post(f"{base_url}/api/auth/logout", json={})
            if response.status_code == 200:
                print("✅ Logout successful")
            else:
                print(f"❌ Logout failed: {response.text}")
        except Exception as e:
            print(f"❌ Logout error: {e}")
    
    return True

async def main():
    """Main test function"""
    print("🧪 Session Flow Test")
    print("Testing: Register → Login → Cart Access → Token Expiry → Refresh → Logout")
    
    success = await test_complete_session_flow()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Session flow test completed!")
    else:
        print("❌ Session flow test failed!")
    
    print("\n💡 Check browser dev tools and server logs for detailed session info")

if __name__ == "__main__":
    asyncio.run(main()) 