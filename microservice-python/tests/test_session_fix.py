#!/usr/bin/env python3
"""
Test Session Fix - Kiểm tra session flow sau khi sửa lỗi
"""

import asyncio
import httpx
import json
import time

API_BASE = "http://localhost:8060"

async def test_session_fix():
    """Test session flow với fix mới"""
    print("🧪 Testing Session Fix")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Login
        print("\n1️⃣ Testing Login...")
        login_response = await client.post(f"{API_BASE}/api/auth/login", json={
            "username": "testuser123",
            "password": "securepass123"
        })
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return
        
        login_data = login_response.json()
        print(f"✅ Login successful")
        print(f"📊 Session info: {login_data.get('expires_in')}s access, {login_data.get('refresh_expires_in')}s refresh")
        
        access_token = login_data.get("access_token")
        refresh_token = login_data.get("refresh_token")
        
        # Test 2: Wait for session to near expiry (20 seconds)
        print(f"\n2️⃣ Waiting 20 seconds (session expires in 30s)...")
        await asyncio.sleep(20)
        
        # Test 3: Test access token still valid
        print("\n3️⃣ Testing access token at 20s mark...")
        profile_response = await client.get(
            f"{API_BASE}/api/auth/profile",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if profile_response.status_code == 200:
            print("✅ Access token still valid at 20s")
        else:
            print(f"⚠️ Access token invalid at 20s: {profile_response.status_code}")
        
        # Test 4: Wait for session to expire (another 15 seconds)
        print(f"\n4️⃣ Waiting another 15 seconds (total 35s, should expire at 30s)...")
        await asyncio.sleep(15)
        
        # Test 5: Test access token expired
        print("\n5️⃣ Testing access token at 35s mark (should be expired)...")
        profile_response = await client.get(
            f"{API_BASE}/api/auth/profile",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if profile_response.status_code == 401:
            print("✅ Access token properly expired at 35s")
            error_data = profile_response.json()
            print(f"📄 Error details: {error_data.get('detail', {}).get('message')}")
        else:
            print(f"⚠️ Expected 401 but got: {profile_response.status_code}")
        
        # Test 6: Test refresh token
        print("\n6️⃣ Testing refresh token...")
        refresh_response = await client.post(f"{API_BASE}/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        if refresh_response.status_code == 200:
            refresh_data = refresh_response.json()
            print("✅ Refresh token works correctly")
            print(f"📊 New session: {refresh_data.get('expires_in')}s access, {refresh_data.get('refresh_expires_in')}s refresh")
            
            new_access_token = refresh_data.get("access_token")
            new_refresh_token = refresh_data.get("refresh_token")
            
            # Test 7: Test new access token
            print("\n7️⃣ Testing new access token...")
            profile_response = await client.get(
                f"{API_BASE}/api/auth/profile",
                headers={"Authorization": f"Bearer {new_access_token}"}
            )
            
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                print("✅ New access token works correctly")
                print(f"👤 User: {profile_data.get('user', {}).get('username')}")
            else:
                print(f"❌ New access token failed: {profile_response.status_code}")
            
            # Test 8: Cleanup - logout
            print("\n8️⃣ Testing logout...")
            logout_response = await client.post(
                f"{API_BASE}/api/auth/logout",
                headers={"Authorization": f"Bearer {new_access_token}"},
                json={"logout_all": True}
            )
            
            if logout_response.status_code == 200:
                print("✅ Logout successful")
            else:
                print(f"⚠️ Logout status: {logout_response.status_code}")
        
        else:
            print(f"❌ Refresh token failed: {refresh_response.status_code}")
            error_data = refresh_response.json()
            print(f"📄 Error: {error_data.get('detail', {}).get('message')}")

async def test_multiple_refresh():
    """Test multiple refresh token calls"""
    print("\n" + "=" * 50)
    print("🔄 Testing Multiple Refresh Calls")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Login
        print("\n1️⃣ Login...")
        login_response = await client.post(f"{API_BASE}/api/auth/login", json={
            "username": "testuser123",
            "password": "securepass123"
        })
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return
        
        login_data = login_response.json()
        refresh_token = login_data.get("refresh_token")
        
        print("✅ Login successful")
        
        # Test multiple refresh calls
        for i in range(3):
            print(f"\n2️⃣.{i+1} Refresh attempt {i+1}...")
            
            refresh_response = await client.post(f"{API_BASE}/api/auth/refresh", json={
                "refresh_token": refresh_token
            })
            
            if refresh_response.status_code == 200:
                refresh_data = refresh_response.json()
                print(f"✅ Refresh {i+1} successful")
                refresh_token = refresh_data.get("refresh_token")  # Use new refresh token
                
                # Test new access token
                new_access_token = refresh_data.get("access_token")
                profile_response = await client.get(
                    f"{API_BASE}/api/auth/profile",
                    headers={"Authorization": f"Bearer {new_access_token}"}
                )
                
                if profile_response.status_code == 200:
                    print(f"✅ New access token {i+1} works")
                else:
                    print(f"❌ New access token {i+1} failed: {profile_response.status_code}")
                
                # Wait 2 seconds between refreshes
                if i < 2:
                    await asyncio.sleep(2)
                    
            else:
                print(f"❌ Refresh {i+1} failed: {refresh_response.status_code}")
                error_data = refresh_response.json()
                print(f"📄 Error: {error_data.get('detail', {}).get('message')}")
                break

async def main():
    """Main test function"""
    try:
        await test_session_fix()
        await test_multiple_refresh()
        
        print("\n" + "=" * 50)
        print("🏁 Session Fix Test Complete!")
        print("✅ Check console logs for detailed flow")
        print("📋 Test Results:")
        print("   - Session expiry timing should work correctly")
        print("   - Refresh token should work when access token expires")
        print("   - Multiple refresh calls should work")
        print("   - Frontend buttons should be more responsive")
        
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 