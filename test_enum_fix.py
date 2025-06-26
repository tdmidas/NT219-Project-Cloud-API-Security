#!/usr/bin/env python3
"""
Test script to verify enum Role fix for SUPER_ADMIN
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'microservice-python'))

from shared.rbac import RBACManager, Role, Permission

def test_enum_mapping():
    """Test that database SUPER_ADMIN maps correctly to enum"""
    print("🧪 Testing Enum Role Mapping Fix\n")
    
    # Test user with database value SUPER_ADMIN
    user_from_db = {
        "rbac_role": "SUPER_ADMIN",  # This is how it's stored in database
        "username": "superadmin"
    }
    
    print(f"📊 Testing user with rbac_role: '{user_from_db['rbac_role']}'")
    
    try:
        # Get role from RBACManager
        role = RBACManager.get_user_role(user_from_db)
        print(f"   ✅ Mapped to Role enum: {role}")
        print(f"   ✅ Role value: {role.value}")
        
        # Check if it's the correct enum
        if role == Role.SUPER_ADMIN:
            print("   ✅ Correctly mapped to Role.SUPER_ADMIN")
        else:
            print(f"   ❌ Incorrectly mapped to {role}")
            
        # Get permissions
        permissions = RBACManager.get_user_permissions(user_from_db)
        print(f"   ✅ Permissions count: {len(permissions)}")
        
        # Check specific permissions
        has_read_users = Permission.READ_USERS in permissions
        has_manage_system = Permission.MANAGE_SYSTEM in permissions
        
        print(f"   ✅ Has READ:users: {has_read_users}")
        print(f"   ✅ Has manage:system: {has_manage_system}")
        
        if has_read_users and has_manage_system:
            print("\n🎉 SUPER_ADMIN enum mapping is working correctly!")
            return True
        else:
            print("\n❌ SUPER_ADMIN missing expected permissions")
            return False
            
    except ValueError as e:
        print(f"   ❌ ValueError when mapping role: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def test_all_roles():
    """Test all role mappings"""
    print("\n🔍 Testing All Role Mappings\n")
    
    test_cases = [
        ("guest", Role.GUEST),
        ("user", Role.USER), 
        ("voucher_creator", Role.VOUCHER_CREATOR),
        ("moderator", Role.MODERATOR),
        ("admin", Role.ADMIN),
        ("SUPER_ADMIN", Role.SUPER_ADMIN)  # Database format
    ]
    
    all_passed = True
    
    for db_value, expected_enum in test_cases:
        test_user = {"rbac_role": db_value}
        try:
            actual_role = RBACManager.get_user_role(test_user)
            if actual_role == expected_enum:
                print(f"   ✅ '{db_value}' -> {expected_enum.name}")
            else:
                print(f"   ❌ '{db_value}' -> {actual_role.name} (expected {expected_enum.name})")
                all_passed = False
        except Exception as e:
            print(f"   ❌ '{db_value}' -> Error: {e}")
            all_passed = False
    
    return all_passed

if __name__ == "__main__":
    print("🚀 Enum Role Mapping Test\n")
    print("=" * 50)
    
    # Test SUPER_ADMIN specifically
    superadmin_ok = test_enum_mapping()
    
    # Test all roles
    all_roles_ok = test_all_roles()
    
    print("\n" + "=" * 50)
    
    if superadmin_ok and all_roles_ok:
        print("✅ All tests passed! Enum mapping is working correctly.")
    else:
        print("❌ Some tests failed. Check the output above.")
    
    print("\n📋 Summary:")
    print("   - Database stores SUPER_ADMIN (uppercase)")
    print("   - Enum Role.SUPER_ADMIN now has value 'SUPER_ADMIN'")
    print("   - RBACManager.get_user_role() can map correctly")
    print("   - SUPER_ADMIN gets all expected permissions")