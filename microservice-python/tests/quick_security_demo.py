#!/usr/bin/env python3
"""
Quick Database Security Demo

Script demo nhanh để hiểu cách hoạt động của 3 tính năng bảo mật:
1. RBAC (Role-Based Access Control)
2. Row Level Security (RLS) 
3. Data Masking

Usage:
    python quick_security_demo.py
"""

import sys
import os
from typing import Dict, Any
from bson import ObjectId

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from shared.database_security import DatabaseSecurityManager
from shared.rbac import RBACManager, Role, Permission
from atlas_config import get_atlas_connection_string

def print_header(title: str):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_subheader(title: str):
    """Print formatted subheader"""
    print(f"\n--- {title} ---")

def create_sample_users():
    """Create sample users for testing"""
    return {
        "guest": {
            "id": "guest123",
            "username": "guest_user",
            "email": "guest@example.com",
            "admin": False,
            "roles": ["guest"]
        },
        "user": {
            "id": "user123",
            "username": "regular_user",
            "email": "user@example.com",
            "admin": False,
            "roles": ["user"]
        },
        "voucher_creator": {
            "id": "creator123",
            "username": "voucher_creator",
            "email": "creator@example.com",
            "admin": False,
            "roles": ["voucher_creator"]
        },
        "admin": {
            "id": "admin123",
            "username": "admin_user",
            "email": "admin@example.com",
            "admin": True,
            "roles": ["admin"]
        },
        "super_admin": {
            "id": "superadmin123",
            "username": "super_admin",
            "email": "superadmin@example.com",
            "admin": True,
            "roles": ["super_admin"]
        }
    }

def demo_rbac():
    """Demo RBAC functionality"""
    print_header("DEMO 1: RBAC (Role-Based Access Control)")
    
    users = create_sample_users()
    
    # Test permissions for each role
    permissions_to_test = [
        Permission.READ_VOUCHERS,
        Permission.CREATE_VOUCHERS,
        Permission.READ_USERS,
        Permission.ADMIN_ACCESS,
        Permission.MANAGE_SYSTEM
    ]
    
    print(f"{'Role':<15} {'Permission':<20} {'Has Access':<10}")
    print("-" * 50)
    
    for role_name, user in users.items():
        # Get user role
        user_role = RBACManager.get_user_role(user)
        print(f"\n{role_name.upper()} (Role: {user_role}):")
        
        for permission in permissions_to_test:
            has_permission = RBACManager.has_permission(user, permission)
            status = "✅ YES" if has_permission else "❌ NO"
            print(f"  {permission:<25} {status}")
    
    # Demo collection access
    print_subheader("Collection Access Control")
    
    collections = ["users", "vouchers", "carts", "sessions"]
    operations = ["read", "write", "delete"]
    
    for role_name, user in users.items():
        print(f"\n{role_name.upper()} collection access:")
        for collection in collections:
            for operation in operations:
                has_access = DatabaseSecurityManager.check_collection_access(
                    user, collection, operation
                )
                status = "✅" if has_access else "❌"
                print(f"  {collection}.{operation}: {status}")

def demo_row_level_security():
    """Demo Row Level Security"""
    print_header("DEMO 2: Row Level Security (RLS)")
    
    users = create_sample_users()
    
    # Test RLS for different collections
    collections = ["users", "carts", "sessions", "vouchers"]
    
    for collection in collections:
        print_subheader(f"RLS for '{collection}' collection")
        
        base_query = {}
        
        for role_name, user in users.items():
            # Apply RLS
            filtered_query = DatabaseSecurityManager.apply_row_level_security(
                user, collection, base_query.copy()
            )
            
            # Create secure query
            secure_query = DatabaseSecurityManager.create_secure_query_filter(
                user, collection, base_query.copy()
            )
            
            print(f"\n{role_name.upper()}:")
            print(f"  Base query: {base_query}")
            print(f"  RLS filtered: {filtered_query}")
            print(f"  Secure query: {secure_query}")
            
            # Explain the filtering
            if filtered_query == base_query:
                print(f"  📝 No filtering applied (admin/super_admin access)")
            else:
                print(f"  📝 Filtered to user's own data only")

def demo_data_masking():
    """Demo Data Masking"""
    print_header("DEMO 3: Data Masking")
    
    users = create_sample_users()
    
    # Sample sensitive data
    sample_data = {
        "user_data": {
            "_id": ObjectId("507f1f77bcf86cd799439012"),
            "username": "john_doe",
            "email": "john.doe@example.com",
            "password": "hashed_password_123456",
            "google_id": "1234567890123456",
            "facebook_id": "9876543210987654",
            "wallet": {
                "balance": 150.75,
                "history": ["payment1", "payment2"]
            }
        },
        "session_data": {
            "_id": ObjectId("507f1f77bcf86cd799439041"),
            "user_id": ObjectId("507f1f77bcf86cd799439012"),
            "token": "jwt_token_abc123def456ghi789jkl012",
            "ip_address": "192.168.1.100",
            "device_info": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "voucher_data": {
            "_id": ObjectId("507f1f77bcf86cd799439021"),
            "title": "50% Off Electronics",
            "description": "Great discount on electronics",
            "affLink": "https://example.com/affiliate/abc123def456",
            "payment": {
                "amount": 25.50,
                "method": "paypal",
                "account": "merchant@example.com"
            }
        }
    }
    
    for data_type, data in sample_data.items():
        print_subheader(f"Masking {data_type}")
        
        print(f"Original data:")
        for key, value in data.items():
            print(f"  {key}: {value}")
        
        for role_name, user in users.items():
            # Test with user as owner (for user_data)
            if data_type == "user_data":
                test_user = user.copy()
                test_user["id"] = str(data["_id"])  # Make user the owner
            else:
                test_user = user
            
            masked_data = DatabaseSecurityManager.mask_sensitive_data(
                data, test_user, "read"
            )
            
            print(f"\n{role_name.upper()} sees:")
            
            # Show what changed
            for key, original_value in data.items():
                if key in masked_data:
                    masked_value = masked_data[key]
                    if str(original_value) != str(masked_value):
                        print(f"  {key}: {original_value} → {masked_value} 🔒")
                    else:
                        print(f"  {key}: {masked_value} ✅")
                else:
                    print(f"  {key}: [REMOVED] 🚫")

def demo_field_masking_examples():
    """Demo specific field masking examples"""
    print_header("DEMO 4: Field Masking Examples")
    
    # Test different field types
    test_fields = {
        "email": "user@example.com",
        "google_id": "1234567890123456",
        "facebook_id": "9876543210987654",
        "token": "jwt_token_abc123def456ghi789",
        "ip_address": "192.168.1.100",
        "device_info": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0",
        "affLink": "https://example.com/affiliate/abc123def456ghi789",
        "wallet": {"balance": 100.50, "history": ["tx1", "tx2"]}
    }
    
    print("Field masking examples:")
    print(f"{'Field':<15} {'Original':<40} {'Masked':<40}")
    print("-" * 100)
    
    for field_name, original_value in test_fields.items():
        masked_value = DatabaseSecurityManager._mask_field_value(original_value, field_name)
        print(f"{field_name:<15} {str(original_value):<40} {str(masked_value):<40}")

def demo_security_integration():
    """Demo how all security features work together"""
    print_header("DEMO 5: Security Integration Example")
    
    print("Scenario: Regular user trying to access user data")
    
    # Create a regular user
    current_user = {
        "id": "user123",
        "username": "regular_user",
        "email": "user@example.com",
        "admin": False,
        "roles": ["user"]
    }
    
    # Sample database query
    collection = "users"
    base_query = {}  # Want to get all users
    
    print(f"\n1. RBAC Check:")
    can_read = DatabaseSecurityManager.check_collection_access(
        current_user, collection, "read"
    )
    print(f"   Can read 'users' collection: {can_read}")
    
    if not can_read:
        print("   ❌ Access denied by RBAC!")
        return
    
    print(f"\n2. Row Level Security:")
    secure_query = DatabaseSecurityManager.create_secure_query_filter(
        current_user, collection, base_query
    )
    print(f"   Original query: {base_query}")
    print(f"   Secure query: {secure_query}")
    print(f"   📝 User can only see their own profile")
    
    print(f"\n3. Data Masking:")
    # Simulate query result
    query_result = {
        "_id": ObjectId("507f1f77bcf86cd799439012"),
        "username": "regular_user",
        "email": "user@example.com",
        "password": "hashed_password",
        "google_id": "1234567890",
        "wallet": {"balance": 100}
    }
    
    masked_result = DatabaseSecurityManager.mask_sensitive_data(
        query_result, current_user, "read"
    )
    
    print(f"   Raw result: {query_result}")
    print(f"   Masked result: {masked_result}")
    print(f"   📝 Since it's user's own data, only password is removed")
    
    print(f"\n4. Audit Logging:")
    DatabaseSecurityManager.log_database_access(
        current_user, collection, "find", secure_query, True
    )
    print(f"   ✅ Database access logged for audit")

def main():
    """Main demo function"""
    print("🔐 Database Security Features Demo")
    print("This demo shows how RBAC, RLS, and Data Masking work together")
    
    try:
        # Run all demos
        demo_rbac()
        demo_row_level_security()
        demo_data_masking()
        demo_field_masking_examples()
        demo_security_integration()
        
        print_header("Demo Completed Successfully! 🎉")
        print("\nKey Takeaways:")
        print("1. 🔑 RBAC controls WHO can access WHAT")
        print("2. 🛡️  RLS controls WHICH DATA users can see")
        print("3. 🎭 Data Masking controls HOW MUCH users can see")
        print("4. 📝 All access is logged for audit")
        print("\nFor comprehensive testing, run: python test_database_security.py")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)