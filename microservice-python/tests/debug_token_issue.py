#!/usr/bin/env python3
"""
Debug script để kiểm tra vấn đề token authentication
"""

import os
import sys
import jwt
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from shared.session_manager import session_manager
from shared.middleware import AuthenticationMiddleware

def debug_token_validation():
    """Debug token validation issues"""
    print("🔍 Token Validation Debug Tool")
    print("=" * 50)
    
    # Get JWT configuration
    jwt_secret = os.getenv("JWT_ACCESS_KEY", "your-secret-key")
    jwt_algorithm = "HS256"
    
    print(f"JWT Secret Key: {jwt_secret}")
    print(f"JWT Algorithm: {jwt_algorithm}")
    print()
    
    # Prompt for token
    token = input("Nhập access token của bạn: ").strip()
    
    if not token:
        print("❌ Không có token được nhập!")
        return
    
    print(f"\n🔑 Token: {token[:20]}...{token[-20:]}")
    print()
    
    # Check 1: Token blacklist
    print("1️⃣ Kiểm tra blacklist...")
    is_blacklisted = session_manager.is_access_token_blacklisted(token)
    if is_blacklisted:
        print("❌ Token đã bị blacklist (đã logout)")
        return
    else:
        print("✅ Token không bị blacklist")
    
    # Check 2: JWT decode
    print("\n2️⃣ Kiểm tra JWT decode...")
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=[jwt_algorithm])
        print("✅ JWT decode thành công")
        print(f"   User ID: {payload.get('user_id')}")
        print(f"   Username: {payload.get('username')}")
        print(f"   Admin: {payload.get('admin')}")
        print(f"   Roles: {payload.get('roles')}")
        
        # Check expiration
        if "exp" in payload:
            exp_time = datetime.utcfromtimestamp(payload["exp"])
            current_time = datetime.utcnow()
            print(f"   Expires at: {exp_time}")
            print(f"   Current time: {current_time}")
            
            if exp_time < current_time:
                print("❌ Token đã hết hạn")
                return
            else:
                print("✅ Token chưa hết hạn")
        
    except jwt.ExpiredSignatureError:
        print("❌ Token đã hết hạn")
        return
    except jwt.InvalidTokenError as e:
        print(f"❌ Token không hợp lệ: {e}")
        return
    except Exception as e:
        print(f"❌ Lỗi decode token: {e}")
        return
    
    # Check 3: Blacklist size
    print("\n3️⃣ Thông tin blacklist...")
    blacklist_size = len(session_manager.blacklisted_tokens)
    print(f"   Số token trong blacklist: {blacklist_size}")
    
    if blacklist_size > 0:
        print("   Một số token trong blacklist:")
        for i, bl_token in enumerate(list(session_manager.blacklisted_tokens)[:3]):
            print(f"   - {bl_token[:20]}...{bl_token[-20:]}")
    
    print("\n✅ Token hợp lệ - không có vấn đề gì được phát hiện!")
    print("\n💡 Gợi ý kiểm tra:")
    print("   1. Đảm bảo JWT_ACCESS_KEY giống nhau giữa auth-service và user-service")
    print("   2. Kiểm tra xem có logout trước đó không")
    print("   3. Kiểm tra network request headers")

if __name__ == "__main__":
    debug_token_validation()