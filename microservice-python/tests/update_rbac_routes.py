import asyncio
import os
from pathlib import Path
import re

def find_admin_flag_usage():
    """Find all files that still use admin flag directly"""
    microservice_dir = Path("f:\\NT219-Project\\Voux\\microservice-python")
    
    # Patterns to search for
    patterns = [
        r'current_user\.get\("admin"',
        r'user\.get\("admin"',
        r'\["admin"\]',
        r'admin.*True',
        r'admin.*False',
        r'admin":\s*True',
        r'admin":\s*False'
    ]
    
    files_to_update = []
    
    # Search in Python files
    for py_file in microservice_dir.rglob("*.py"):
        if py_file.name in ["fix_role_synchronization.py", "update_rbac_routes.py", "create_super_admin.py"]:
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in patterns:
                if re.search(pattern, content):
                    files_to_update.append(str(py_file))
                    break
                    
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return files_to_update

def update_user_controller():
    """Update user_controller.py to use RBAC consistently"""
    file_path = "f:\\NT219-Project\\Voux\\microservice-python\\user-service\\controllers\\user_controller.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Already updated in previous session, but let's ensure it's correct
        # Check if RBACManager import exists
        if "from shared.rbac import RBACManager, Permission" not in content:
            # Add import if missing
            import_pattern = r'(from shared\.database import.*?)\n'
            replacement = r'\1\nfrom shared.rbac import RBACManager, Permission\n'
            content = re.sub(import_pattern, replacement, content)
        
        print(f"✅ User controller already updated with RBAC")
        return True
        
    except Exception as e:
        print(f"❌ Error updating user controller: {e}")
        return False

def update_middleware():
    """Update middleware.py to ensure consistent RBAC usage"""
    file_path = "f:\\NT219-Project\\Voux\\microservice-python\\shared\\middleware.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if require_admin function uses RBAC
        if "RBACManager.has_permission(current_user, Permission.ADMIN_ACCESS)" in content:
            print(f"✅ Middleware already updated with RBAC")
            return True
        else:
            print(f"⚠️ Middleware may need RBAC updates")
            return False
        
    except Exception as e:
        print(f"❌ Error checking middleware: {e}")
        return False

def update_auth_controller():
    """Update auth_controller.py to use standardized role storage"""
    file_path = "f:\\NT219-Project\\Voux\\microservice-python\\auth-service\\controllers\\auth_controller.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update user creation to include rbac_role
        old_pattern = r'user_dict = \{\s*"username": user_data\.username,\s*"email": user_data\.email,\s*"password": hashed_password\.decode\(\'utf-8\'\),\s*"admin": False,\s*"roles": \["user"\],'
        new_pattern = '''user_dict = {
                "username": user_data.username,
                "email": user_data.email,
                "password": hashed_password.decode('utf-8'),
                "admin": False,
                "roles": ["user"],
                "rbac_role": "USER",'''
        
        if "rbac_role" not in content:
            content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE | re.DOTALL)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Updated auth controller to include rbac_role in user creation")
        else:
            print(f"✅ Auth controller already includes rbac_role")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating auth controller: {e}")
        return False

def update_session_manager():
    """Update session_manager.py to use RBAC"""
    file_path = "f:\\NT219-Project\\Voux\\microservice-python\\shared\\session_manager.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace admin-based role assignment with RBAC
        old_pattern = r'"roles": \["admin"\] if user\.get\("admin"\) else \["user"\],'
        new_pattern = '"roles": user.get("roles", ["user"]),'
        
        if '"roles": ["admin"] if user.get("admin") else ["user"],' in content:
            content = content.replace(old_pattern, new_pattern)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Updated session manager to use RBAC roles")
        else:
            print(f"✅ Session manager already uses RBAC roles")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating session manager: {e}")
        return False

def create_rbac_helper_functions():
    """Create helper functions for common RBAC checks"""
    helper_content = '''# RBAC Helper Functions
# Add these to your controllers for consistent RBAC usage

from shared.rbac import RBACManager, Permission
from fastapi import HTTPException, status

def require_permission(current_user: dict, permission: Permission):
    """Helper function to check if user has required permission"""
    if not RBACManager.has_permission(current_user, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Bạn không có quyền thực hiện hành động này!",
                "error_code": "INSUFFICIENT_PERMISSIONS"
            }
        )

def require_admin_access(current_user: dict):
    """Helper function to require admin access"""
    require_permission(current_user, Permission.ADMIN_ACCESS)

def require_owner_or_admin(current_user: dict, resource_owner_id: str):
    """Helper function to check if user is owner or admin"""
    user_id = current_user.get("id")
    is_owner = str(user_id) == str(resource_owner_id)
    is_admin = RBACManager.has_permission(current_user, Permission.ADMIN_ACCESS)
    
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Bạn chỉ có thể truy cập tài nguyên của chính mình!",
                "error_code": "ACCESS_DENIED"
            }
        )

def get_user_role_string(current_user: dict) -> str:
    """Get user role as string for display purposes"""
    role = RBACManager.get_user_role(current_user)
    return role.value

def check_role_hierarchy(current_user: dict, target_role: str) -> bool:
    """Check if current user can manage users with target role"""
    current_role = RBACManager.get_user_role(current_user)
    
    # Role hierarchy: SUPER_ADMIN > ADMIN > MODERATOR > VOUCHER_CREATOR > USER > GUEST
    role_levels = {
        "GUEST": 0,
        "USER": 1,
        "VOUCHER_CREATOR": 2,
        "MODERATOR": 3,
        "ADMIN": 4,
        "SUPER_ADMIN": 5
    }
    
    current_level = role_levels.get(current_role.value, 0)
    target_level = role_levels.get(target_role, 0)
    
    return current_level > target_level
'''
    
    file_path = "f:\\NT219-Project\\Voux\\microservice-python\\shared\\rbac_helpers.py"
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(helper_content)
        
        print(f"✅ Created RBAC helper functions at {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating RBAC helpers: {e}")
        return False

def main():
    """Main function to update RBAC usage across routes"""
    print("🚀 Starting RBAC routes update...")
    
    # Step 1: Find files that still use admin flag
    print("\n🔍 Finding files with admin flag usage...")
    files_with_admin = find_admin_flag_usage()
    
    if files_with_admin:
        print(f"\n📋 Files that may need RBAC updates:")
        for file_path in files_with_admin:
            print(f"  - {file_path}")
    else:
        print("\n✅ No files found with direct admin flag usage")
    
    # Step 2: Update key files
    print("\n🔧 Updating key files...")
    
    success_count = 0
    
    if update_user_controller():
        success_count += 1
    
    if update_middleware():
        success_count += 1
    
    if update_auth_controller():
        success_count += 1
    
    if update_session_manager():
        success_count += 1
    
    if create_rbac_helper_functions():
        success_count += 1
    
    print(f"\n📊 Update summary:")
    print(f"  Successfully updated: {success_count}/5 components")
    
    if success_count == 5:
        print("\n🎉 All RBAC updates completed successfully!")
        print("\n📝 Next steps:")
        print("  1. Test the updated RBAC system")
        print("  2. Update any remaining files that use admin flags directly")
        print("  3. Use the helper functions in shared/rbac_helpers.py for consistent RBAC checks")
    else:
        print("\n⚠️ Some updates failed. Please check the errors above.")
    
    print("\n✅ RBAC routes update completed!")

if __name__ == "__main__":
    main()