import asyncio
import os
from dotenv import load_dotenv
from shared.database import Database, AuthDatabase
from shared.rbac import Role, RBACManager
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_current_data_structure():
    """Analyze current user data structure in database"""
    try:
        # Connect to database
        auth_db_uri = os.getenv("AUTH_DB_URI")
        await Database.connect_to_mongo("auth", auth_db_uri)
        users_collection = AuthDatabase.get_collection("users")
        
        print("🔍 Analyzing current user data structure...")
        
        # Get all users
        users = await users_collection.find({}).to_list(length=None)
        
        print(f"\n📊 Found {len(users)} users in database")
        print("\n🔍 Data structure analysis:")
        
        structure_types = {
            "has_rbac_role": 0,
            "has_roles_array": 0,
            "has_admin_flag": 0,
            "inconsistent": []
        }
        
        for user in users:
            username = user.get("username", "unknown")
            has_rbac_role = "rbac_role" in user
            has_roles_array = "roles" in user
            has_admin_flag = "admin" in user
            
            if has_rbac_role:
                structure_types["has_rbac_role"] += 1
            if has_roles_array:
                structure_types["has_roles_array"] += 1
            if has_admin_flag:
                structure_types["has_admin_flag"] += 1
                
            # Check for inconsistencies
            if has_rbac_role and has_roles_array:
                rbac_role = user.get("rbac_role")
                roles_array = user.get("roles", [])
                
                # Convert rbac_role to expected array format
                expected_role = rbac_role.lower() if rbac_role else "user"
                if expected_role == "super_admin":
                    expected_role = "super_admin"
                    
                if expected_role not in roles_array:
                    structure_types["inconsistent"].append({
                        "username": username,
                        "rbac_role": rbac_role,
                        "roles_array": roles_array,
                        "admin": user.get("admin", False)
                    })
            
            print(f"  {username}: rbac_role={user.get('rbac_role', 'None')}, roles={user.get('roles', 'None')}, admin={user.get('admin', 'None')}")
        
        print(f"\n📈 Structure summary:")
        print(f"  Users with rbac_role field: {structure_types['has_rbac_role']}")
        print(f"  Users with roles array: {structure_types['has_roles_array']}")
        print(f"  Users with admin flag: {structure_types['has_admin_flag']}")
        print(f"  Inconsistent users: {len(structure_types['inconsistent'])}")
        
        if structure_types["inconsistent"]:
            print("\n⚠️ Inconsistent users found:")
            for user in structure_types["inconsistent"]:
                print(f"  {user['username']}: rbac_role={user['rbac_role']}, roles={user['roles_array']}, admin={user['admin']}")
        
        return structure_types
        
    except Exception as e:
        logger.error(f"Error analyzing data structure: {e}")
        return None
    finally:
        await Database.close_mongo_connection()

async def standardize_role_storage():
    """Standardize role storage to use unified approach"""
    try:
        # Connect to database
        auth_db_uri = os.getenv("AUTH_DB_URI")
        await Database.connect_to_mongo("auth", auth_db_uri)
        users_collection = AuthDatabase.get_collection("users")
        
        print("\n🔧 Standardizing role storage...")
        
        # Get all users
        users = await users_collection.find({}).to_list(length=None)
        
        updates_made = 0
        
        for user in users:
            username = user.get("username", "unknown")
            user_id = user["_id"]
            
            # Determine the correct role based on current data
            current_role = None
            
            # Priority 1: Check rbac_role field
            if "rbac_role" in user:
                current_role = user["rbac_role"]
            # Priority 2: Check admin flag
            elif user.get("admin", False):
                current_role = "ADMIN"
            # Priority 3: Check roles array
            elif "roles" in user and user["roles"]:
                roles_array = user["roles"]
                if "super_admin" in roles_array:
                    current_role = "SUPER_ADMIN"
                elif "admin" in roles_array:
                    current_role = "ADMIN"
                elif "moderator" in roles_array:
                    current_role = "MODERATOR"
                elif "voucher_creator" in roles_array:
                    current_role = "VOUCHER_CREATOR"
                else:
                    current_role = "USER"
            else:
                current_role = "USER"
            
            # Convert role to proper format
            role_mapping = {
                "SUPER_ADMIN": "super_admin",
                "ADMIN": "admin", 
                "MODERATOR": "moderator",
                "VOUCHER_CREATOR": "voucher_creator",
                "USER": "user"
            }
            
            standardized_role = role_mapping.get(current_role, "user")
            
            # Prepare update data
            update_data = {
                "rbac_role": current_role,
                "roles": [standardized_role],
                "admin": current_role in ["ADMIN", "SUPER_ADMIN"]
            }
            
            # Check if update is needed
            needs_update = (
                user.get("rbac_role") != current_role or
                user.get("roles") != [standardized_role] or
                user.get("admin") != update_data["admin"]
            )
            
            if needs_update:
                result = await users_collection.update_one(
                    {"_id": user_id},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    updates_made += 1
                    print(f"  ✅ Updated {username}: role={current_role}, roles=[{standardized_role}], admin={update_data['admin']}")
                else:
                    print(f"  ❌ Failed to update {username}")
            else:
                print(f"  ⏭️ {username} already standardized")
        
        print(f"\n✅ Standardization complete! Updated {updates_made} users.")
        return updates_made
        
    except Exception as e:
        logger.error(f"Error standardizing role storage: {e}")
        return 0
    finally:
        await Database.close_mongo_connection()

async def verify_rbac_consistency():
    """Verify RBAC consistency after standardization"""
    try:
        # Connect to database
        auth_db_uri = os.getenv("AUTH_DB_URI")
        await Database.connect_to_mongo("auth", auth_db_uri)
        users_collection = AuthDatabase.get_collection("users")
        
        print("\n🔍 Verifying RBAC consistency...")
        
        # Get all users
        users = await users_collection.find({}).to_list(length=None)
        
        consistent_users = 0
        inconsistent_users = []
        
        for user in users:
            username = user.get("username", "unknown")
            rbac_role = user.get("rbac_role", "USER")
            roles_array = user.get("roles", ["user"])
            admin_flag = user.get("admin", False)
            
            # Check consistency
            expected_admin = rbac_role in ["ADMIN", "SUPER_ADMIN"]
            expected_role_in_array = {
                "SUPER_ADMIN": "super_admin",
                "ADMIN": "admin",
                "MODERATOR": "moderator", 
                "VOUCHER_CREATOR": "voucher_creator",
                "USER": "user"
            }.get(rbac_role, "user")
            
            is_consistent = (
                admin_flag == expected_admin and
                expected_role_in_array in roles_array
            )
            
            if is_consistent:
                consistent_users += 1
                print(f"  ✅ {username}: CONSISTENT")
            else:
                inconsistent_users.append({
                    "username": username,
                    "rbac_role": rbac_role,
                    "roles": roles_array,
                    "admin": admin_flag,
                    "expected_admin": expected_admin,
                    "expected_role": expected_role_in_array
                })
                print(f"  ❌ {username}: INCONSISTENT")
        
        print(f"\n📊 Consistency report:")
        print(f"  Consistent users: {consistent_users}")
        print(f"  Inconsistent users: {len(inconsistent_users)}")
        
        if inconsistent_users:
            print("\n⚠️ Inconsistent users details:")
            for user in inconsistent_users:
                print(f"  {user['username']}:")
                print(f"    Current: rbac_role={user['rbac_role']}, roles={user['roles']}, admin={user['admin']}")
                print(f"    Expected: admin={user['expected_admin']}, role_in_array={user['expected_role']}")
        
        return len(inconsistent_users) == 0
        
    except Exception as e:
        logger.error(f"Error verifying RBAC consistency: {e}")
        return False
    finally:
        await Database.close_mongo_connection()

async def main():
    """Main function to fix role synchronization"""
    print("🚀 Starting role synchronization fix...")
    
    # Step 1: Analyze current structure
    structure_info = await analyze_current_data_structure()
    if not structure_info:
        print("❌ Failed to analyze data structure")
        return
    
    # Step 2: Standardize role storage
    updates_made = await standardize_role_storage()
    print(f"\n📈 Made {updates_made} updates")
    
    # Step 3: Verify consistency
    is_consistent = await verify_rbac_consistency()
    
    if is_consistent:
        print("\n🎉 All users are now consistent!")
    else:
        print("\n⚠️ Some inconsistencies remain. Please check the details above.")
    
    print("\n✅ Role synchronization fix completed!")

if __name__ == "__main__":
    asyncio.run(main())