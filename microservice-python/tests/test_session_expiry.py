#!/usr/bin/env python3
"""
Test Session Expiry (30 seconds)
Demo phiên đăng nhập hết hạn sau 30 giây
"""

import asyncio
import httpx
import time
import json
from datetime import datetime

# Test configuration
API_GATEWAY_URL = "http://localhost:8060"
AUTH_SERVICE_URL = "http://localhost:3001"

async def test_session_expiry():
    """Test 30-second session expiry"""
    print("⏰ Testing 30-Second Session Expiry")
    print("=" * 60)
    
    # Test data
    test_user = {
        "username": f"sessiontest_{int(time.time())}",
        "email": f"session_{int(time.time())}@example.com",
        "password": "securepass123"
    }
    
    async with httpx.AsyncClient() as client:
        
        # Step 1: Register user
        print("\n📝 Step 1: Registering test user...")
        
        register_response = await client.post(
            f"{API_GATEWAY_URL}/api/auth/register",
            json=test_user,
            timeout=10
        )
        
        if register_response.status_code != 200:
            print("❌ Registration failed!")
            print(f"Response: {register_response.json()}")
            return
        
        print("✅ User registered successfully")
        
        # Step 2: Login and get 30-second token
        print("\n🔐 Step 2: Logging in (getting 30-second session)...")
        
        login_response = await client.post(
            f"{API_GATEWAY_URL}/api/auth/login",
            json={
                "username": test_user["username"],
                "password": test_user["password"],
                "remember_me": False
            },
            timeout=10
        )
        
        if login_response.status_code != 200:
            print("❌ Login failed!")
            return
        
        login_data = login_response.json()
        access_token = login_data["access_token"]
        expires_in = login_data["expires_in"]
        session_warning = login_data.get("session_warning", "")
        
        print(f"✅ Login successful!")
        print(f"📊 Session expires in: {expires_in} seconds")
        print(f"⚠️ Warning: {session_warning}")
        print(f"🎟️ Access Token: {access_token[:50]}...")
        
        # Step 3: Test valid token (immediately after login)
        print("\n🔍 Step 3: Testing valid token (immediately after login)...")
        
        profile_response = await client.get(
            f"{API_GATEWAY_URL}/api/auth/profile",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print(f"✅ Token valid! Username: {profile_data['user']['username']}")
        else:
            print(f"❌ Token invalid: {profile_response.status_code}")
        
        # Step 4: Wait for token to expire (30 seconds)
        print(f"\n⏳ Step 4: Waiting for token to expire ({expires_in} seconds)...")
        
        for remaining in range(expires_in, 0, -1):
            print(f"   ⏰ Token expires in: {remaining} seconds", end="\r")
            await asyncio.sleep(1)
        
        print("\n   🕐 Token should now be expired!")
        
        # Step 5: Test expired token
        print("\n🚨 Step 5: Testing expired token...")
        
        expired_response = await client.get(
            f"{API_GATEWAY_URL}/api/auth/profile",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        print(f"Status Code: {expired_response.status_code}")
        
        if expired_response.status_code == 401:
            error_data = expired_response.json()
            print("✅ Token expired correctly!")
            print(f"📢 Error Message: {error_data.get('detail', {}).get('message', 'No message')}")
            print(f"🔍 Error Code: {error_data.get('detail', {}).get('error_code', 'No code')}")
            print(f"🎯 Action Required: {error_data.get('detail', {}).get('action_required', 'No action')}")
            
            if error_data.get('detail', {}).get('session_expired'):
                print("✅ Session expiry flag detected!")
        else:
            print("❌ Token should have expired but didn't!")
            print(f"Response: {expired_response.json()}")
        
        # Step 6: Test refresh token
        print("\n🔄 Step 6: Testing refresh token...")
        
        refresh_token = login_data.get("refresh_token")
        if refresh_token:
            refresh_response = await client.post(
                f"{API_GATEWAY_URL}/api/auth/refresh",
                json={"refresh_token": refresh_token},
                timeout=10
            )
            
            if refresh_response.status_code == 200:
                refresh_data = refresh_response.json()
                new_access_token = refresh_data["access_token"]
                print("✅ Token refresh successful!")
                print(f"🎟️ New Token: {new_access_token[:50]}...")
                print(f"⚠️ Warning: {refresh_data.get('session_warning', '')}")
                
                # Test new token
                new_profile_response = await client.get(
                    f"{API_GATEWAY_URL}/api/auth/profile",
                    headers={"Authorization": f"Bearer {new_access_token}"},
                    timeout=10
                )
                
                if new_profile_response.status_code == 200:
                    print("✅ New token works correctly!")
                else:
                    print("❌ New token doesn't work!")
                    
            else:
                print(f"❌ Token refresh failed: {refresh_response.status_code}")
                print(f"Response: {refresh_response.json()}")
        else:
            print("❌ No refresh token received!")

async def test_multiple_requests():
    """Test multiple API requests with short session"""
    print("\n\n🔄 Testing Multiple API Requests with Short Session")
    print("=" * 60)
    
    # Use existing test user credentials
    test_user = {
        "username": "testuser123",
        "password": "securepass123"
    }
    
    async with httpx.AsyncClient() as client:
        
        # Login
        login_response = await client.post(
            f"{API_GATEWAY_URL}/api/auth/login",
            json={
                "username": test_user["username"],
                "password": test_user["password"],
                "remember_me": False
            },
            timeout=10
        )
        
        if login_response.status_code != 200:
            print("❌ Login failed for multiple requests test!")
            return
        
        login_data = login_response.json()
        access_token = login_data["access_token"]
        
        print(f"✅ Logged in for multiple requests test")
        
        # Make requests every 10 seconds for 1 minute
        for i in range(6):  # 6 requests over 1 minute
            print(f"\n📊 Request {i+1}/6 (after {i*10} seconds)...")
            
            if i > 0:
                await asyncio.sleep(10)
            
            # Test profile endpoint
            response = await client.get(
                f"{API_GATEWAY_URL}/api/auth/profile",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Request {i+1} successful")
            elif response.status_code == 401:
                error_data = response.json()
                print(f"❌ Request {i+1} failed - Session expired!")
                print(f"📢 Message: {error_data.get('detail', {}).get('message', 'No message')}")
                break
            else:
                print(f"❌ Request {i+1} failed with status: {response.status_code}")

async def main():
    """Main test function"""
    print("🧪 Session Expiry Test Suite (30 seconds)")
    print("=" * 60)
    
    # Test 1: Basic session expiry
    await test_session_expiry()
    
    # Wait a bit
    await asyncio.sleep(3)
    
    # Test 2: Multiple requests
    await test_multiple_requests()
    
    print("\n" + "=" * 60)
    print("🏁 Session expiry tests completed!")
    print("\n💡 Summary:")
    print("- Access tokens now expire in 30 seconds")
    print("- Users get Vietnamese error messages when session expires")
    print("- Refresh tokens expire in 5 minutes (for demo)")
    print("- All endpoints will automatically logout users after 30s")

if __name__ == "__main__":
    asyncio.run(main()) 