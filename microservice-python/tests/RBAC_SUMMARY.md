# 🛡️ RBAC Implementation Summary

## Overview

Voux Microservices sử dụng Role-Based Access Control (RBAC) system để quản lý quyền truy cập chi tiết cho tất cả endpoints.

## 🏗️ RBAC Architecture

### Role Hierarchy (Thứ tự quyền hạn)

```
GUEST → USER → VOUCHER_CREATOR → MODERATOR → ADMIN → SUPER_ADMIN
```

### Permission Categories

#### 👤 User Permissions
- `READ_USERS` - Xem danh sách người dùng
- `CREATE_USERS` - Tạo người dùng mới  
- `UPDATE_USERS` - Cập nhật thông tin người dùng
- `DELETE_USERS` - Xóa người dùng
- `UPDATE_OWN_PROFILE` - Cập nhật profile của chính mình

#### 🎫 Voucher Permissions
- `READ_VOUCHERS` - Xem voucher (public)
- `CREATE_VOUCHERS` - Tạo voucher mới
- `UPDATE_VOUCHERS` - Cập nhật bất kỳ voucher nào
- `DELETE_VOUCHERS` - Xóa bất kỳ voucher nào
- `UPDATE_OWN_VOUCHERS` - Cập nhật voucher của chính mình
- `DELETE_OWN_VOUCHERS` - Xóa voucher của chính mình

#### 🛒 Cart Permissions
- `READ_OWN_CART` - Xem giỏ hàng của mình
- `MANAGE_OWN_CART` - Quản lý giỏ hàng của mình

#### 👨‍💼 Admin Permissions
- `ADMIN_ACCESS` - Truy cập vào chức năng admin
- `MANAGE_SYSTEM` - Quản lý hệ thống
- `VIEW_ANALYTICS` - Xem báo cáo thống kê

#### 🔐 Session Permissions
- `MANAGE_OWN_SESSIONS` - Quản lý phiên đăng nhập của mình
- `MANAGE_ALL_SESSIONS` - Quản lý tất cả phiên đăng nhập

## 📋 Permission Matrix

| Role                | Permissions                                                                                        |
| ------------------- | -------------------------------------------------------------------------------------------------- |
| **GUEST**           | `READ_VOUCHERS`                                                                                    |
| **USER**            | `READ_VOUCHERS`, `READ_OWN_CART`, `MANAGE_OWN_CART`, `UPDATE_OWN_PROFILE`, `MANAGE_OWN_SESSIONS`   |
| **VOUCHER_CREATOR** | User permissions + `CREATE_VOUCHERS`, `UPDATE_OWN_VOUCHERS`, `DELETE_OWN_VOUCHERS`                 |
| **MODERATOR**       | Voucher Creator permissions + `READ_USERS`, `UPDATE_VOUCHERS`, `DELETE_VOUCHERS`, `VIEW_ANALYTICS` |
| **ADMIN**           | Most permissions except Super Admin exclusives                                                     |
| **SUPER_ADMIN**     | **ALL PERMISSIONS**                                                                                |

## 🔧 Implementation Details

### Service-by-Service RBAC

#### Auth Service (`/api/auth/*`)
- **Public endpoints:** register, login, refresh, verify
- **User endpoints:** profile, change-password, sessions (with `MANAGE_OWN_SESSIONS`)
- **Admin endpoints:** admin sessions management (with `MANAGE_ALL_SESSIONS`)

#### User Service (`/api/users/*`)
- **GET /users** → Requires `READ_USERS` (Admin only)
- **GET /users/{id}** → Public profile view
- **PUT /users/{id}** → Requires `UPDATE_USERS` OR (ownership + `UPDATE_OWN_PROFILE`)
- **DELETE /users/{id}** → Requires `DELETE_USERS` (Admin only)
- **GET /users/stats** → Requires `VIEW_ANALYTICS`

#### Voucher Service (`/api/vouchers/*`)
- **Public endpoints:** getAllVoucher, search, categories (no auth required)
- **POST /createVoucher** → Requires `CREATE_VOUCHERS`
- **PUT /updateVoucher/{id}** → Requires `UPDATE_VOUCHERS` OR (ownership + `UPDATE_OWN_VOUCHERS`)
- **DELETE /deleteVoucher/{id}** → Requires `DELETE_VOUCHERS` OR (ownership + `DELETE_OWN_VOUCHERS`)
- **GET /admin/stats** → Requires `VIEW_ANALYTICS`

#### Cart Service (`/api/cart/*`)
- **All cart operations** → Require `READ_OWN_CART` or `MANAGE_OWN_CART`
- **Admin endpoints** → Require `READ_USERS`, `UPDATE_USERS`, or `VIEW_ANALYTICS`

## 🛠️ Technical Implementation

### RBACManager Class
```python
class RBACManager:
    @staticmethod
    def get_user_role(user: Dict) -> Role
    
    @staticmethod
    def get_user_permissions(user: Dict) -> Set[Permission]
    
    @staticmethod
    def has_permission(user: Dict, permission: Permission) -> bool
    
    @staticmethod
    def can_access_resource(user: Dict, resource_owner_id: str, 
                          required_permission: Permission, 
                          ownership_permission: Permission) -> bool
```

### Permission Middleware
- `require_permission_dep(permission)` - FastAPI dependency
- `require_ownership_or_permission()` - Decorator cho resource ownership
- `require_admin()` - FastAPI dependency cho admin access

### Usage Examples

```python
# Require specific permission
@router.get("/admin/stats", dependencies=[Depends(require_permission_dep(Permission.VIEW_ANALYTICS))])

# Resource ownership check
@router.put("/vouchers/{voucher_id}")
async def update_voucher(voucher_id: str, current_user: dict = Depends(get_current_user)):
    # Check if user can update: admin OR (owner + permission)
    can_update_any = RBACManager.has_permission(current_user, Permission.UPDATE_VOUCHERS)
    can_update_own = (RBACManager.has_permission(current_user, Permission.UPDATE_OWN_VOUCHERS) 
                     and current_user.get("id") == voucher_owner_id)
    
    if not (can_update_any or can_update_own):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
```

## 🚨 Security Features

### 1. **Ownership-Based Access Control**
- Users can only modify their own resources (vouchers, profile, cart)
- Admins can modify any resource
- Automatic ownership verification

### 2. **Permission Inheritance**
- Higher roles inherit permissions from lower roles
- SUPER_ADMIN has all permissions automatically

### 3. **Granular Permissions**
- Separate read/write permissions
- Own vs. any resource permissions
- Session management permissions

### 4. **Error Handling**
- Consistent 403 Forbidden responses
- Detailed permission requirements in error messages
- No information leakage

## 📊 Permission Flow Examples

### Scenario 1: Regular User Updates Profile
```
User Role: USER
Action: PUT /api/users/profile/me
Required Permission: UPDATE_OWN_PROFILE
✅ ALLOWED - User has UPDATE_OWN_PROFILE permission
```

### Scenario 2: Regular User Tries Admin Action
```
User Role: USER  
Action: GET /api/users/stats/overview
Required Permission: VIEW_ANALYTICS
❌ DENIED - User lacks VIEW_ANALYTICS permission
```

### Scenario 3: User Updates Own Voucher
```
User Role: VOUCHER_CREATOR
Action: PUT /api/vouchers/updateVoucher/{id}
Ownership: User owns this voucher
Required Permission: UPDATE_OWN_VOUCHERS OR UPDATE_VOUCHERS
✅ ALLOWED - User has UPDATE_OWN_VOUCHERS and owns resource
```

### Scenario 4: Admin Updates Any Voucher  
```
User Role: ADMIN
Action: PUT /api/vouchers/updateVoucher/{id}  
Ownership: User does NOT own this voucher
Required Permission: UPDATE_VOUCHERS
✅ ALLOWED - Admin has UPDATE_VOUCHERS permission
```

## 🔄 Role Assignment

### Default Assignment
- New users get `USER` role automatically
- Admin status controlled by `admin: true` field
- Roles array: `["user"]` or `["admin"]`

### Role Promotion (Future Enhancement)
```javascript
// MongoDB command to promote user
db.users.updateOne(
  {"username": "user123"},
  {
    $set: {
      "roles": ["voucher_creator"],  // or ["moderator"], ["admin"]
      "admin": false  // true for admin/super_admin
    }
  }
)
```

## 🎯 Testing RBAC

### Permission Testing Checklist
- [ ] Public endpoints work without auth
- [ ] Protected endpoints require valid tokens  
- [ ] Users can access their own resources
- [ ] Users cannot access others' resources
- [ ] Admins can access any resource
- [ ] Role hierarchy works correctly
- [ ] Error responses are consistent

### Test Users for Different Roles
```json
{
  "guest": "No authentication",
  "user": "Regular user account", 
  "voucher_creator": "User with voucher creation rights",
  "moderator": "User with moderation rights",
  "admin": "Admin with most permissions",
  "super_admin": "Full system access"
}
```

## 🚀 Benefits

1. **Security** - Granular access control
2. **Scalability** - Easy to add new permissions
3. **Maintainability** - Centralized permission logic
4. **Flexibility** - Role-based + ownership-based access
5. **Auditability** - Clear permission trails

---

**🔐 Security Note:** Always test permission boundaries thoroughly. The RBAC system is designed to be secure by default - users have minimal permissions unless explicitly granted. 