#!/usr/bin/env python3
"""
Script chẩn đoán chi tiết vấn đề INVALID_TOKEN
"""

import os
import sys
import requests
import json
import jwt
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_services_health():
    """Kiểm tra tình trạng các service"""
    print("🏥 Kiểm tra tình trạng các service...")
    print("=" * 50)
    
    services = {
        "Auth Service": os.getenv("AUTH_SERVICE_URL", "http://localhost:3001"),
        "User Service": os.getenv("USER_SERVICE_URL", "http://localhost:3002"),
        "Voucher Service": os.getenv("VOUCHER_SERVICE_URL", "http://localhost:3003"),
        "Cart Service": os.getenv("CART_SERVICE_URL", "http://localhost:3004")
    }
    
    for service_name, url in services.items():
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name}: OK ({url})")
            else:
                print(f"⚠️  {service_name}: Status {response.status_code} ({url})")
        except Exception as e:
            print(f"❌ {service_name}: OFFLINE ({url}) - {e}")
    print()

def test_login_and_get_token():
    """Test login và lấy token mới"""
    print("🔐 Test login để lấy token mới...")
    print("=" * 50)
    
    auth_url = os.getenv("AUTH_SERVICE_URL", "http://localhost:3001")
    
    # Test credentials
    test_users = [
        {"username": "testuser", "password": "securepass123"},
        {"username": "admin", "password": "admin123"},
        {"username": "user1", "password": "password123"}
    ]
    
    for user_creds in test_users:
        print(f"🧪 Thử đăng nhập với: {user_creds['username']}")
        try:
            response = requests.post(
                f"{auth_url}/api/auth/login",
                json=user_creds,
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and "access_token" in result:
                    token = result["access_token"]
                    print(f"   ✅ Login thành công!")
                    print(f"   🔑 Token: {token[:30]}...")
                    return token
                else:
                    print(f"   ❌ Login thất bại: {result}")
            else:
                try:
                    error = response.json()
                    print(f"   ❌ Error: {error}")
                except:
                    print(f"   ❌ Raw response: {response.text}")
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        print()
    
    return None

def analyze_token(token):
    """Phân tích token"""
    print("🔍 Phân tích token...")
    print("=" * 50)
    
    if not token:
        print("❌ Không có token để phân tích!")
        return
    
    print(f"Token length: {len(token)}")
    print(f"Token preview: {token[:50]}...{token[-20:]}")
    print()
    
    # Decode without verification first
    try:
        header = jwt.get_unverified_header(token)
        print(f"📋 Token Header: {json.dumps(header, indent=2)}")
        
        payload = jwt.decode(token, options={"verify_signature": False})
        print(f"📋 Token Payload: {json.dumps(payload, indent=2, default=str)}")
        
        # Check expiration
        if "exp" in payload:
            exp_time = datetime.fromtimestamp(payload["exp"])
            now = datetime.now()
            print(f"⏰ Expires at: {exp_time}")
            print(f"⏰ Current time: {now}")
            if exp_time < now:
                print("❌ Token đã hết hạn!")
            else:
                print(f"✅ Token còn hiệu lực ({exp_time - now} remaining)")
        
    except Exception as e:
        print(f"❌ Lỗi khi decode token: {e}")
    print()

def test_token_with_services(token):
    """Test token với các service"""
    print("🧪 Test token với các service...")
    print("=" * 50)
    
    if not token:
        print("❌ Không có token để test!")
        return
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    test_endpoints = [
        ("User Service", os.getenv("USER_SERVICE_URL", "http://localhost:3002"), "/api/users/"),
        ("User Service", os.getenv("USER_SERVICE_URL", "http://localhost:3002"), "/api/users/profile/me"),
        ("Voucher Service", os.getenv("VOUCHER_SERVICE_URL", "http://localhost:3003"), "/api/vouchers/"),
        ("Cart Service", os.getenv("CART_SERVICE_URL", "http://localhost:3004"), "/api/cart/")
    ]
    
    for service_name, base_url, endpoint in test_endpoints:
        print(f"🔗 Testing {service_name}{endpoint}")
        try:
            response = requests.get(
                f"{base_url}{endpoint}",
                headers=headers,
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Success")
                try:
                    result = response.json()
                    if "data" in result:
                        print(f"   📊 Data items: {len(result.get('data', []))}")
                except:
                    pass
            else:
                print(f"   ❌ Failed")
                try:
                    error = response.json()
                    print(f"   📝 Error: {json.dumps(error, indent=6)}")
                    
                    # Specific analysis for INVALID_TOKEN
                    if isinstance(error, dict):
                        if error.get("detail", {}).get("error_code") == "INVALID_TOKEN":
                            print(f"   🎯 INVALID_TOKEN detected!")
                            print(f"   💡 Possible causes:")
                            print(f"      - JWT_ACCESS_KEY mismatch between services")
                            print(f"      - Token format issues")
                            print(f"      - Token signature verification failed")
                            
                except:
                    print(f"   📝 Raw response: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        print()

def check_jwt_config():
    """Kiểm tra cấu hình JWT"""
    print("⚙️  Kiểm tra cấu hình JWT...")
    print("=" * 50)
    
    jwt_key = os.getenv("JWT_ACCESS_KEY")
    jwt_refresh_key = os.getenv("JWT_REFRESH_KEY")
    
    print(f"JWT_ACCESS_KEY: {jwt_key}")
    print(f"JWT_REFRESH_KEY: {jwt_refresh_key}")
    
    if not jwt_key:
        print("❌ JWT_ACCESS_KEY không được thiết lập!")
    else:
        print(f"✅ JWT_ACCESS_KEY length: {len(jwt_key)}")
    print()

def main():
    """Main function"""
    print("🔧 VOUX Token Diagnostic Tool")
    print("=" * 60)
    print()
    
    # 1. Check services health
    check_services_health()
    
    # 2. Check JWT config
    check_jwt_config()
    
    # 3. Try to get a fresh token
    token = test_login_and_get_token()
    
    # 4. Analyze token if we got one
    if token:
        analyze_token(token)
        test_token_with_services(token)
    else:
        print("❌ Không thể lấy token mới. Kiểm tra:")
        print("   1. Auth service có đang chạy không?")
        print("   2. Database connection có OK không?")
        print("   3. Test user credentials có đúng không?")
        print()
        
        # Still test with user-provided token
        user_token = input("Nhập token hiện tại của bạn (hoặc Enter để bỏ qua): ").strip()
        if user_token:
            analyze_token(user_token)
            test_token_with_services(user_token)
    
    print("\n🎯 Tóm tắt khuyến nghị:")
    print("=" * 50)
    print("1. Nếu thấy INVALID_TOKEN:")
    print("   - Restart tất cả services")
    print("   - Đảm bảo JWT_ACCESS_KEY giống nhau trong .env")
    print("   - Login lại để lấy token mới")
    print("2. Nếu token hết hạn:")
    print("   - Login lại")
    print("3. Nếu service offline:")
    print("   - Khởi động lại service")
    print("   - Kiểm tra port conflicts")
    print("4. Nếu vẫn lỗi:")
    print("   - Kiểm tra database connection")
    print("   - Xem logs chi tiết của service")

if __name__ == "__main__":
    main()