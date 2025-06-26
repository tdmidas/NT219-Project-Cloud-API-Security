#!/usr/bin/env python3
"""
Test script cho Event-Driven User Synchronization
"""

import asyncio
import httpx
import time
import json
from datetime import datetime

# Test configuration
API_GATEWAY_URL = "http://localhost:8060"
AUTH_SERVICE_URL = "http://localhost:3001"
USER_SERVICE_URL = "http://localhost:3002"

async def test_event_sync():
    """Test complete user registration and sync flow"""
    print("🧪 Testing Event-Driven User Synchronization")
    print("=" * 60)
    
    # Test data
    test_user = {
        "username": f"testuser_{int(time.time())}",
        "email": f"test_{int(time.time())}@example.com",
        "password": "securepass123"
    }
    
    async with httpx.AsyncClient() as client:
        
        # Step 1: Register user trong Auth Service
        print("\n📝 Step 1: Registering user in Auth Service...")
        
        register_response = await client.post(
            f"{API_GATEWAY_URL}/api/auth/register",
            json=test_user,
            timeout=10
        )
        
        print(f"Status: {register_response.status_code}")
        print(f"Response: {register_response.json()}")
        
        if register_response.status_code != 200:
            print("❌ Registration failed!")
            return
        
        print("✅ User registered in Auth Service")
        
        # Step 2: Login để lấy user_id
        print("\n🔐 Step 2: Logging in to get user details...")
        
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
        user_id = login_data["user"]["id"]
        access_token = login_data["access_token"]
        
        print(f"✅ Login successful. User ID: {user_id}")
        
        # Step 3: Wait for event processing
        print("\n⏳ Step 3: Waiting for event processing (5 seconds)...")
        await asyncio.sleep(5)
        
        # Step 4: Check if user exists in User Service
        print("\n🔍 Step 4: Checking if user synced to User Service...")
        
        user_response = await client.get(
            f"{API_GATEWAY_URL}/api/users/{user_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        print(f"Status: {user_response.status_code}")
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            print("✅ User found in User Service!")
            print(f"Username: {user_data['user']['username']}")
            print(f"Email: {user_data['user']['email']}")
            print(f"Synced from auth: {user_data['user'].get('synced_from_auth', 'Not marked')}")
            
            # Step 5: Verify data consistency
            print("\n🔄 Step 5: Verifying data consistency...")
            
            auth_username = test_user["username"]
            sync_username = user_data['user']['username']
            
            if auth_username == sync_username:
                print("✅ Data consistency verified!")
                print("\n🎉 EVENT-DRIVEN SYNC TEST PASSED!")
            else:
                print("❌ Data inconsistency detected!")
                print(f"Auth: {auth_username}, Synced: {sync_username}")
                
        else:
            print("❌ User not found in User Service!")
            print("Event sync might have failed")
            
        # Step 6: Test User Service endpoints
        print("\n📊 Step 6: Testing User Service functionality...")
        
        users_list_response = await client.get(
            f"{API_GATEWAY_URL}/api/users/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        if users_list_response.status_code == 403:
            print("✅ User Service RBAC working (403 for non-admin)")
        else:
            print(f"Users list status: {users_list_response.status_code}")

async def test_rabbitmq_connection():
    """Test RabbitMQ connectivity"""
    print("\n🐰 Testing RabbitMQ Management UI...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:15672/api/overview",
                auth=("admin", "password"),
                timeout=5
            )
            
            if response.status_code == 200:
                print("✅ RabbitMQ Management UI accessible")
                data = response.json()
                print(f"RabbitMQ Version: {data.get('rabbitmq_version', 'Unknown')}")
            else:
                print(f"❌ RabbitMQ Management UI error: {response.status_code}")
                
    except Exception as e:
        print(f"❌ RabbitMQ connection failed: {e}")

async def main():
    """Main test function"""
    print("🚀 Event-Driven User Sync Test Suite")
    print("=" * 60)
    
    # Test RabbitMQ first
    await test_rabbitmq_connection()
    
    # Wait a bit
    await asyncio.sleep(2)
    
    # Test full sync flow
    await test_event_sync()
    
    print("\n" + "=" * 60)
    print("🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(main()) 