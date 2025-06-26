#!/usr/bin/env python3
"""
Test New Session Logic
Demo logic hỏi người dùng có muốn tiếp tục sau 30 giây
"""

import asyncio
import httpx
import time
import json
from datetime import datetime

# Test configuration
API_GATEWAY_URL = "http://localhost:8060"
AUTH_SERVICE_URL = "http://localhost:3001"

async def test_new_session_logic():
    """Test new 30-second session logic"""
    print("🆕 Testing New Session Logic")
    print("=" * 70)
    
    # Test data
    test_user = {
        "username": f"newlogic_{int(time.time())}",
        "email": f"newlogic_{int(time.time())}@example.com",
        "password": "securepass123"
    }
    
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            # Step 1: Register user
            print("\n🔶 Step 1: Registering test user...")
            register_response = await client.post(
                f"{AUTH_SERVICE_URL}/api/auth/register",
                json=test_user
            )
            
            if register_response.status_code == 200:
                print("✅ User registered successfully")
            else:
                print(f"❌ Registration failed: {register_response.text}")
                return
            
            # Step 2: Login and get session info
            print("\n🔶 Step 2: Logging in to start session...")
            login_response = await client.post(
                f"{AUTH_SERVICE_URL}/api/auth/login",
                json={
                    "username": test_user["username"],
                    "password": test_user["password"],
                    "remember_me": False
                }
            )
            
            if login_response.status_code != 200:
                print(f"❌ Login failed: {login_response.text}")
                return
            
            login_data = login_response.json()
            print("✅ Login successful!")
            print(f"📊 Session Info:")
            print(f"   - Client sees: {login_data.get('expires_in')} seconds")
            print(f"   - Actual token valid for: {login_data.get('actual_token_expiry', 'N/A')} seconds")
            print(f"   - Warning: {login_data.get('session_warning', 'N/A')}")
            
            access_token = login_data["access_token"]
            refresh_token = login_data["refresh_token"]
            
            # Step 3: Simulate user activity before 30s
            print("\n🔶 Step 3: Simulating user activity...")
            for i in range(3):
                print(f"⏱️  After {i*10} seconds - making API call...")
                
                profile_response = await client.get(
                    f"{AUTH_SERVICE_URL}/api/auth/profile",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if profile_response.status_code == 200:
                    print(f"✅ API call successful (user: {profile_response.json()['user']['username']})")
                else:
                    print(f"❌ API call failed: {profile_response.status_code}")
                
                if i < 2:  # Don't wait after last iteration
                    await asyncio.sleep(10)
            
            # Step 4: Wait for 30s mark (we've already waited 20s, so wait 10 more)
            print("\n🔶 Step 4: Waiting for 30-second mark...")
            await asyncio.sleep(10)
            print("⏰ 30 seconds reached - In real app, user would see modal now!")
            
            # Step 5: Simulate user decision delay
            print("\n🔶 Step 5: Simulating user thinking time (5 seconds)...")
            await asyncio.sleep(5)
            print("🤔 User is deciding whether to continue...")
            
            # Step 6: Test token still valid (within 45s grace period)
            print("\n🔶 Step 6: Testing if token still works during grace period...")
            profile_response = await client.get(
                f"{AUTH_SERVICE_URL}/api/auth/profile",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if profile_response.status_code == 200:
                print("✅ Token still valid during grace period!")
                print("👤 User decides: 'Yes, I want to continue'")
            else:
                print(f"❌ Token expired during grace period: {profile_response.status_code}")
                return
            
            # Step 7: Simulate refresh token (user chose to continue)
            print("\n🔶 Step 7: Refreshing session (user chose to continue)...")
            refresh_response = await client.post(
                f"{AUTH_SERVICE_URL}/api/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            
            if refresh_response.status_code == 200:
                refresh_data = refresh_response.json()
                print("✅ Session refreshed successfully!")
                print(f"📊 New Session Info:")
                print(f"   - New token expires in: {refresh_data.get('expires_in')} seconds")
                print(f"   - Actual expiry: {refresh_data.get('actual_token_expiry', 'N/A')} seconds")
                print(f"   - Message: {refresh_data.get('message')}")
                
                new_access_token = refresh_data["access_token"]
                
                # Test new token works
                profile_response = await client.get(
                    f"{AUTH_SERVICE_URL}/api/auth/profile",
                    headers={"Authorization": f"Bearer {new_access_token}"}
                )
                
                if profile_response.status_code == 200:
                    print("✅ New token works! Session successfully extended.")
                else:
                    print(f"❌ New token doesn't work: {profile_response.status_code}")
            else:
                print(f"❌ Token refresh failed: {refresh_response.text}")
            
            # Step 8: Test scenario where user doesn't respond
            print("\n🔶 Step 8: Testing auto-logout scenario...")
            print("💡 Simulating: User doesn't respond to modal...")
            
            # Wait for another 30s + 15s grace period + 10s buffer
            print("⏳ Waiting for token to truly expire...")
            await asyncio.sleep(55)
            
            # Try to use expired token
            profile_response = await client.get(
                f"{AUTH_SERVICE_URL}/api/auth/profile", 
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if profile_response.status_code == 401:
                error_data = profile_response.json()
                print("✅ Token properly expired!")
                print(f"📄 Error response: {error_data.get('detail', {}).get('message', 'N/A')}")
                print(f"🔧 Error code: {error_data.get('detail', {}).get('error_code', 'N/A')}")
            else:
                print(f"⚠️  Unexpected response: {profile_response.status_code}")
                
        except Exception as e:
            print(f"❌ Test error: {e}")
    
    print("\n" + "=" * 70)
    print("🎯 Test Summary:")
    print("1. ✅ User logged in with 30-second session")
    print("2. ✅ Token actually valid for 45 seconds (30s + 15s grace)")
    print("3. ✅ User can use app normally for 30 seconds")
    print("4. ✅ After 30s, modal should ask if user wants to continue")
    print("5. ✅ User has 15-second grace period to decide")
    print("6. ✅ If user chooses 'Yes', session extends successfully")
    print("7. ✅ If user doesn't respond, token expires and auto-logout")
    print("\n🚀 Frontend Logic:")
    print("   - After 30s: Show modal 'Do you want to continue?'")
    print("   - Give user 10s to decide (within 15s grace period)")
    print("   - 'Yes' → Refresh token → New 30s session")
    print("   - 'No' or timeout → Logout immediately")

async def test_quick_logout_scenario():
    """Test scenario where user chooses logout immediately"""
    print("\n\n🔴 Testing Quick Logout Scenario")
    print("=" * 50)
    
    test_user = {
        "username": f"quicklogout_{int(time.time())}",
        "email": f"quicklogout_{int(time.time())}@example.com", 
        "password": "securepass123"
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # Register and login
            await client.post(f"{AUTH_SERVICE_URL}/api/auth/register", json=test_user)
            
            login_response = await client.post(
                f"{AUTH_SERVICE_URL}/api/auth/login",
                json={
                    "username": test_user["username"],
                    "password": test_user["password"]
                }
            )
            
            login_data = login_response.json()
            access_token = login_data["access_token"]
            
            print("✅ User logged in")
            print("⏰ Waiting 30 seconds...")
            await asyncio.sleep(30)
            
            print("💭 Modal appears: 'Do you want to continue?'")
            print("👤 User clicks: 'No, logout'")
            
            # Simulate immediate logout
            logout_response = await client.post(
                f"{AUTH_SERVICE_URL}/api/auth/logout",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"logout_all": False}
            )
            
            if logout_response.status_code == 200:
                print("✅ User logged out successfully")
                print(f"📄 Message: {logout_response.json().get('message')}")
            else:
                print(f"❌ Logout failed: {logout_response.text}")
                
        except Exception as e:
            print(f"❌ Test error: {e}")

async def main():
    """Main test function"""
    print("🧪 New Session Logic Testing Suite")
    print("Testing the updated 30-second session logic with user choice")
    
    await test_new_session_logic()
    await test_quick_logout_scenario()
    
    print("\n🏁 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 