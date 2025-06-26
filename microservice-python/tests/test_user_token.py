#!/usr/bin/env python3
"""
Script test token cụ thể của user
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_user_token():
    """Test token cụ thể của user"""
    print("🔍 User Token Tester")
    print("=" * 50)
    
    # Get service URL
    user_service_url = os.getenv("USER_SERVICE_URL", "http://localhost:3002")
    print(f"User Service URL: {user_service_url}")
    print()
    
    # Prompt for token
    token = input("Nhập access token của bạn: ").strip()
    
    if not token:
        print("❌ Không có token được nhập!")
        return
    
    print(f"\n🔑 Testing token: {token[:20]}...{token[-20:]}")
    print()
    
    # Test different endpoints
    endpoints = [
        ("/api/users/", "GET all users"),
        ("/api/users/profile/me", "GET own profile"),
        ("/health", "Health check (no auth required)")
    ]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    for endpoint, description in endpoints:
        print(f"🧪 Testing {description}...")
        print(f"   Endpoint: {endpoint}")
        
        try:
            if endpoint == "/health":
                # Health check without auth
                response = requests.get(
                    f"{user_service_url}{endpoint}",
                    timeout=10
                )
            else:
                # Authenticated endpoints
                response = requests.get(
                    f"{user_service_url}{endpoint}",
                    headers=headers,
                    timeout=10
                )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Success")
                result = response.json()
                if isinstance(result, dict):
                    if "data" in result:
                        print(f"   📊 Data count: {len(result.get('data', []))}")
                    elif "success" in result:
                        print(f"   📊 Success: {result.get('success')}")
            else:
                print(f"   ❌ Failed")
                try:
                    error_detail = response.json()
                    print(f"   📝 Error: {json.dumps(error_detail, indent=6)}")
                except:
                    print(f"   📝 Raw response: {response.text}")
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        print()
    
    # Additional debug info
    print("🔧 Debug Information:")
    print(f"   JWT_ACCESS_KEY: {os.getenv('JWT_ACCESS_KEY')}")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'not set')}")
    print()
    
    print("💡 Nếu token bị từ chối:")
    print("   1. Kiểm tra token có đúng format Bearer không")
    print("   2. Kiểm tra token có bị blacklist không (đã logout)")
    print("   3. Kiểm tra JWT_ACCESS_KEY giống nhau giữa auth và user service")
    print("   4. Restart user service sau khi thay đổi .env")
    print("   5. Login lại để lấy token mới")

if __name__ == "__main__":
    test_user_token()