#!/usr/bin/env python3
"""
Test script for login-logout-login cycle to detect hanging issues
"""

import asyncio
import httpx
import time
import json
from datetime import datetime

# Test configuration
API_GATEWAY_URL = "http://localhost:8060"

async def test_login_logout_cycle():
    """Test login -> logout -> login cycle"""
    print("🧪 Testing Login-Logout-Login Cycle")
    print("=" * 50)
    
    # Test credentials (use existing user or create one)
    test_creds = {
        "username": "testuser123",
        "password": "securepass123",
        "remember_me": False
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Step 1: First Login
        print("\n🔐 Step 1: First login...")
        
        try:
            login_response = await client.post(
                f"{API_GATEWAY_URL}/api/auth/login",
                json=test_creds,
                timeout=10
            )
            
            print(f"Status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                access_token = login_data["access_token"]
                print("✅ First login successful")
            else:
                print(f"❌ First login failed: {login_response.text}")
                return
                
        except Exception as e:
            print(f"❌ First login error: {e}")
            return
        
        # Step 2: Logout
        print("\n👋 Step 2: Logout...")
        
        try:
            logout_response = await client.post(
                f"{API_GATEWAY_URL}/api/auth/logout",
                headers={"Authorization": f"Bearer {access_token}"},
                json={"logout_all": True},
                timeout=10
            )
            
            print(f"Status: {logout_response.status_code}")
            
            if logout_response.status_code == 200:
                print("✅ Logout successful")
            else:
                print(f"⚠️ Logout failed: {logout_response.text}")
                
        except Exception as e:
            print(f"❌ Logout error: {e}")
        
        # Step 3: Wait a bit
        print("\n⏳ Step 3: Waiting 2 seconds...")
        await asyncio.sleep(2)
        
        # Step 4: Second Login (this was causing the hang)
        print("\n🔐 Step 4: Second login (potential hang point)...")
        
        try:
            start_time = time.time()
            
            login_response = await client.post(
                f"{API_GATEWAY_URL}/api/auth/login",
                json=test_creds,
                timeout=15  # Longer timeout to detect hangs
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            print(f"Status: {login_response.status_code}")
            print(f"Response time: {response_time:.2f} seconds")
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                print("✅ Second login successful!")
                print(f"Username: {login_data['user']['username']}")
                print(f"Token expires in: {login_data['expires_in']} seconds")
            else:
                print(f"❌ Second login failed: {login_response.text}")
                
        except asyncio.TimeoutError:
            print("❌ Second login TIMED OUT - this indicates a hang!")
            return
        except Exception as e:
            print(f"❌ Second login error: {e}")
            return
        
        # Step 5: Quick profile check
        print("\n👤 Step 5: Profile check...")
        
        try:
            profile_response = await client.get(
                f"{API_GATEWAY_URL}/api/auth/profile",
                headers={"Authorization": f"Bearer {login_data['access_token']}"},
                timeout=5
            )
            
            if profile_response.status_code == 200:
                print("✅ Profile check successful")
            else:
                print(f"⚠️ Profile check failed: {profile_response.status_code}")
                
        except Exception as e:
            print(f"❌ Profile check error: {e}")

async def test_multiple_cycles():
    """Test multiple login-logout cycles"""
    print("\n🔄 Testing Multiple Cycles (5 times)")
    print("=" * 50)
    
    for i in range(5):
        print(f"\n--- Cycle {i+1}/5 ---")
        await test_login_logout_cycle()
        await asyncio.sleep(1)

async def main():
    """Main test function"""
    print("🚀 Login-Logout Cycle Test")
    print("=" * 50)
    
    # Single cycle test
    await test_login_logout_cycle()
    
    # Multiple cycles test
    await test_multiple_cycles()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 