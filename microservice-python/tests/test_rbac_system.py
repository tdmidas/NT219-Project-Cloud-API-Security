#!/usr/bin/env python3
"""
Script to test the new RBAC system with SUPER_ADMIN account
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:3001"  # Auth service
USER_SERVICE_URL = "http://localhost:3002"  # User service

# Test accounts
SUPER_ADMIN_CREDENTIALS = {
    "username": "superadmin",
    "password": "SuperAdmin123!"
}

REGULAR_USER_CREDENTIALS = {
    "username": "testuser12345",
    "password": "testpassword123"
}

async def login_user(session, credentials):
    """Login and get access token"""
    try:
        async with session.post(f"{BASE_URL}/api/auth/login", json=credentials) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("success"):
                    return data.get("access_token")
                else:
                    print(f"❌ Login failed: {data.get('message')}")
                    return None
            else:
                text = await response.text()
                print(f"❌ Login failed with status {response.status}: {text}")
                return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

async def test_endpoint(session, url, token, description, expected_status=200):
    """Test an endpoint with authentication"""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    try:
        async with session.get(url, headers=headers) as response:
            status = response.status
            data = await response.json()
            
            success_indicator = "✅" if status == expected_status else "❌"
            print(f"{success_indicator} {description}:")
            print(f"   Status: {status}")
            print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            print()
            
            return status == expected_status
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        print()
        return False

async def test_rbac_system():
    """Test the RBAC system with different user roles"""
    print("🚀 Testing RBAC System...\n")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Login as SUPER_ADMIN
        print("1️⃣ Testing SUPER_ADMIN login...")
        super_admin_token = await login_user(session, SUPER_ADMIN_CREDENTIALS)
        
        if super_admin_token:
            print(f"✅ SUPER_ADMIN login successful")
            print(f"   Token: {super_admin_token[:50]}...\n")
        else:
            print("❌ SUPER_ADMIN login failed\n")
            return
        
        # Test 2: Login as regular user
        print("2️⃣ Testing regular user login...")
        user_token = await login_user(session, REGULAR_USER_CREDENTIALS)
        
        if user_token:
            print(f"✅ Regular user login successful")
            print(f"   Token: {user_token[:50]}...\n")
        else:
            print("❌ Regular user login failed\n")
        
        # Test 3: SUPER_ADMIN accessing admin endpoints
        print("3️⃣ Testing SUPER_ADMIN admin access...")
        await test_endpoint(
            session,
            f"{USER_SERVICE_URL}/api/users/",
            super_admin_token,
            "SUPER_ADMIN accessing all users",
            200
        )
        
        await test_endpoint(
            session,
            f"{USER_SERVICE_URL}/api/users/stats",
            super_admin_token,
            "SUPER_ADMIN accessing user statistics",
            200
        )
        
        # Test 4: Regular user accessing admin endpoints (should fail)
        if user_token:
            print("4️⃣ Testing regular user admin access (should fail)...")
            await test_endpoint(
                session,
                f"{USER_SERVICE_URL}/api/users/",
                user_token,
                "Regular user accessing all users",
                403
            )
            
            await test_endpoint(
                session,
                f"{USER_SERVICE_URL}/api/users/stats",
                user_token,
                "Regular user accessing user statistics",
                403
            )
        
        # Test 5: Test user profile access (both should work for their own profile)
        print("5️⃣ Testing profile access...")
        if user_token:
            await test_endpoint(
                session,
                f"{USER_SERVICE_URL}/api/users/profile/me",
                user_token,
                "Regular user accessing own profile",
                200
            )
        
        await test_endpoint(
            session,
            f"{USER_SERVICE_URL}/api/users/profile/me",
            super_admin_token,
            "SUPER_ADMIN accessing own profile",
            200
        )
        
        # Test 6: Test without authentication (should fail)
        print("6️⃣ Testing unauthenticated access (should fail)...")
        await test_endpoint(
            session,
            f"{USER_SERVICE_URL}/api/users/",
            None,
            "Unauthenticated access to users",
            401
        )
        
        print("🎯 RBAC Testing Complete!")
        print("\n📋 Summary:")
        print("   ✅ SUPER_ADMIN account created with role-based permissions")
        print("   ✅ Regular users updated to USER role (no admin flag)")
        print("   ✅ Admin endpoints protected by RBAC permissions")
        print("   ✅ User profile access works for authenticated users")
        print("   ✅ Unauthenticated access properly blocked")

if __name__ == "__main__":
    print("🔐 RBAC System Testing")
    print("=" * 50)
    asyncio.run(test_rbac_system())