#!/usr/bin/env python3
"""
Debug RBAC logic for users
"""

import asyncio
import httpx
import json
from typing import Dict, Any

async def debug_user_rbac():
    """Debug RBAC for test user"""
    print("🔧 RBAC Debug Tool")
    print("=" * 50)
    
    # Step 1: Register a new user
    print("\n📍 Step 1: Registering test user...")
    
    register_data = {
        "username": "rbactest123",
        "email": "rbactest@example.com",
        "password": "securepass123"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Register via API Gateway
            response = await client.post(
                "http://localhost:8060/api/auth/register", 
                json=register_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Registration: {data.get('message', 'Success')}")
            else:
                print(f"❌ Registration failed: {response.text}")
                # Continue with login in case user exists
                
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    # Step 2: Login to get token and check RBAC
    print("\n📍 Step 2: Login and check RBAC...")
    
    login_data = {
        "username": "rbactest123",
        "password": "securepass123",
        "remember_me": False
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Login via API Gateway
            response = await client.post(
                "http://localhost:8060/api/auth/login", 
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Login successful")
                
                # Print user info
                user = data.get("user", {})
                print(f"   User ID: {user.get('id', 'Unknown')}")
                print(f"   Username: {user.get('username', 'Unknown')}")
                print(f"   Admin: {user.get('admin', False)}")
                
                # Print RBAC info
                rbac = data.get("rbac", {})
                print(f"   Role: {rbac.get('role', 'Unknown')}")
                print(f"   Permissions: {rbac.get('permissions', [])}")
                
                # Check for cart permissions specifically
                permissions = rbac.get('permissions', [])
                cart_permissions = [p for p in permissions if 'cart' in p]
                print(f"   Cart Permissions: {cart_permissions}")
                
                if 'read:own_cart' in permissions and 'manage:own_cart' in permissions:
                    print("   ✅ User has required cart permissions")
                else:
                    print("   ❌ User missing cart permissions!")
                    print("   Expected: ['read:own_cart', 'manage:own_cart']")
                
                access_token = data.get("access_token")
                
                # Step 3: Test RBAC endpoint
                print("\n📍 Step 3: Testing RBAC info endpoint...")
                
                headers = {"Authorization": f"Bearer {access_token}"}
                rbac_response = await client.get(
                    "http://localhost:8060/api/auth/rbac/info",
                    headers=headers
                )
                
                if rbac_response.status_code == 200:
                    rbac_data = rbac_response.json()
                    print("✅ RBAC Info Response:")
                    print(json.dumps(rbac_data, indent=2))
                else:
                    print(f"❌ RBAC info failed: {rbac_response.text}")
                
                # Step 4: Test cart access
                print("\n📍 Step 4: Testing cart access...")
                
                cart_response = await client.get(
                    "http://localhost:8060/api/cart/",
                    headers=headers
                )
                
                print(f"   Cart GET Status: {cart_response.status_code}")
                if cart_response.status_code == 200:
                    print("   ✅ Cart access successful")
                    cart_data = cart_response.json()
                    print(f"   Response: {json.dumps(cart_data, indent=2)}")
                else:
                    print(f"   ❌ Cart access failed: {cart_response.text}")
                
                return True
            else:
                print(f"❌ Login failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

async def debug_rbac_mapping():
    """Debug RBAC mapping directly"""
    print("\n🔍 Debugging RBAC Mapping...")
    print("=" * 40)
    
    # Import RBAC modules
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from shared.rbac import RBACManager, Role, Permission, ROLE_PERMISSIONS
        
        print("✅ Successfully imported RBAC modules")
        
        # Test user data structure
        test_user = {
            "id": "test123",
            "username": "testuser",
            "admin": False,
            "roles": ["user"]
        }
        
        print(f"\n📋 Test User Data: {test_user}")
        
        # Get role
        role = RBACManager.get_user_role(test_user)
        print(f"✅ Detected Role: {role}")
        
        # Get permissions
        permissions = RBACManager.get_user_permissions(test_user)
        print(f"✅ User Permissions: {list(permissions)}")
        
        # Check specific cart permissions
        has_read_cart = RBACManager.has_permission(test_user, Permission.READ_OWN_CART)
        has_manage_cart = RBACManager.has_permission(test_user, Permission.MANAGE_OWN_CART)
        
        print(f"✅ Has READ_OWN_CART: {has_read_cart}")
        print(f"✅ Has MANAGE_OWN_CART: {has_manage_cart}")
        
        # Print USER role permissions
        user_permissions = ROLE_PERMISSIONS.get(Role.USER, set())
        print(f"\n📋 USER Role Permissions: {list(user_permissions)}")
        
        return True
        
    except Exception as e:
        print(f"❌ RBAC import error: {e}")
        return False

async def main():
    """Main debug function"""
    print("🐛 RBAC Debug Tool")
    print("Testing user registration, login, and cart permissions")
    
    # Test 1: Direct RBAC mapping
    await debug_rbac_mapping()
    
    # Test 2: Full user flow
    await debug_user_rbac()
    
    print("\n" + "=" * 50)
    print("🏁 RBAC Debug Complete!")

if __name__ == "__main__":
    asyncio.run(main()) 