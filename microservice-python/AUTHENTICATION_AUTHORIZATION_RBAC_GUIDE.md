# Hướng Dẫn Chi Tiết Authentication và Authorization với RBAC

## Mục Lục
1. [Tổng Quan Hệ Thống](#tổng-quan-hệ-thống)
2. [Cấu Trúc RBAC](#cấu-trúc-rbac)
3. [JWT Authentication](#jwt-authentication)
4. [Session Management](#session-management)
5. [Database Security](#database-security)
6. [Middleware và Decorators](#middleware-và-decorators)
7. [Authentication Controller](#authentication-controller)
8. [Security Features](#security-features)

## Tổng Quan Hệ Thống

Hệ thống Voux Microservices sử dụng JWT (JSON Web Token) kết hợp với RBAC (Role-Based Access Control) để quản lý xác thực và phân quyền người dùng. Kiến trúc được thiết kế theo mô hình microservices với Auth Service làm trung tâm.

### Kiến Trúc Chính:
- **Auth Service**: Dịch vụ xác thực trung tâm (Port 3001)
- **JWT Authentication**: Sử dụng PyJWT 2.8.0 cho token management
- **Session Management**: Quản lý phiên với refresh tokens
- **RBAC System**: Hệ thống phân quyền dựa trên vai trò

---

## Cấu Trúc RBAC

### 1. Định Nghĩa Permissions và Roles

**File: `shared/rbac.py`**

```python
class Permission(Enum):
    # User permissions
    READ_USERS = "read_users"
    CREATE_USERS = "create_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"
    UPDATE_OWN_PROFILE = "update_own_profile"
    
    # Voucher permissions
    READ_VOUCHERS = "read_vouchers"
    CREATE_VOUCHERS = "create_vouchers"
    UPDATE_VOUCHERS = "update_vouchers"
    DELETE_VOUCHERS = "delete_vouchers"
    UPDATE_OWN_VOUCHERS = "update_own_vouchers"
    DELETE_OWN_VOUCHERS = "delete_own_vouchers"
    
    # Cart permissions
    READ_OWN_CART = "read_own_cart"
    MANAGE_OWN_CART = "manage_own_cart"
    
    # Admin permissions
    ADMIN_ACCESS = "admin_access"
    MANAGE_SYSTEM = "manage_system"
    VIEW_ANALYTICS = "view_analytics"
    
    # Session permissions
    MANAGE_OWN_SESSIONS = "manage_own_sessions"
    MANAGE_ALL_SESSIONS = "manage_all_sessions"
```

**Giải thích:**
- **Permission Enum**: Định nghĩa tất cả các quyền trong hệ thống
- **Phân loại quyền**: Chia thành các nhóm User, Voucher, Cart, Admin, Session
- **Naming Convention**: Sử dụng format `ACTION_RESOURCE` (ví dụ: `READ_USERS`, `CREATE_VOUCHERS`)
- **Own vs All**: Phân biệt quyền trên tài nguyên của mình (`OWN`) và tất cả (`ALL`)

```python
class Role(Enum):
    GUEST = "guest"
    USER = "user"
    VOUCHER_CREATOR = "voucher_creator"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
```

**Giải thích:**
- **Role Hierarchy**: Từ GUEST (thấp nhất) đến SUPER_ADMIN (cao nhất)
- **Scalable Design**: Dễ dàng thêm role mới khi cần
- **Clear Naming**: Tên role rõ ràng, dễ hiểu

### 2. Permission Matrix

```python
ROLE_PERMISSIONS = {
    Role.GUEST: [
        Permission.READ_VOUCHERS
    ],
    Role.USER: [
        Permission.READ_VOUCHERS,
        Permission.READ_OWN_CART,
        Permission.MANAGE_OWN_CART,
        Permission.UPDATE_OWN_PROFILE,
        Permission.MANAGE_OWN_SESSIONS
    ],
    Role.VOUCHER_CREATOR: [
        # Kế thừa quyền USER + thêm quyền tạo voucher
        Permission.CREATE_VOUCHERS,
        Permission.UPDATE_OWN_VOUCHERS,
        Permission.DELETE_OWN_VOUCHERS
    ],
    Role.ADMIN: [
        # Tất cả permissions
        Permission.ADMIN_ACCESS,
        Permission.MANAGE_SYSTEM,
        Permission.VIEW_ANALYTICS
    ]
}
```

**Giải thích:**
- **Dictionary Mapping**: Mỗi role được map với list các permissions
- **Inheritance Logic**: Role cao hơn kế thừa quyền của role thấp hơn
- **Granular Control**: Kiểm soát chi tiết từng quyền cụ thể
- **Extensible**: Dễ dàng thêm permission mới cho role

### 3. RBAC Manager Implementation

```python
class RBACManager:
    def __init__(self):
        self.role_permissions = ROLE_PERMISSIONS
    
    def get_user_role(self, user_data: Dict[str, Any]) -> Role:
        """Xác định role của user từ user data"""
        role_str = user_data.get("role", "guest")
        try:
            return Role(role_str)
        except ValueError:
            return Role.GUEST  # Default fallback
```

**Giải thích:**
- **Safe Role Extraction**: Lấy role từ user data với fallback an toàn
- **Default to GUEST**: Nếu role không hợp lệ, mặc định là GUEST
- **Type Safety**: Sử dụng Enum để đảm bảo type safety

```python
    def get_user_permissions(self, user_data: Dict[str, Any]) -> Set[Permission]:
        """Lấy tất cả permissions của user dựa trên role"""
        role = self.get_user_role(user_data)
        return set(self.role_permissions.get(role, []))
```

**Giải thích:**
- **Permission Aggregation**: Tập hợp tất cả quyền của user
- **Set Data Structure**: Sử dụng Set để tránh duplicate và tối ưu lookup
- **Role-based Lookup**: Tra cứu permissions dựa trên role

```python
    def has_permission(self, user_data: Dict[str, Any], required_permission: Permission) -> bool:
        """Kiểm tra user có permission cụ thể không"""
        user_permissions = self.get_user_permissions(user_data)
        return required_permission in user_permissions
```

**Giải thích:**
- **Permission Check**: Kiểm tra user có quyền cụ thể hay không
- **Boolean Return**: Trả về True/False rõ ràng
- **Efficient Lookup**: Sử dụng Set membership cho performance tốt

---

## JWT Authentication

### 1. JWT Middleware

**File: `shared/middleware.py`**

```python
class AuthMiddleware:
    """Enhanced JWT Authentication middleware with session management"""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.jwt_secret = os.getenv("JWT_ACCESS_KEY", "your-secret-key")
        self.jwt_algorithm = "HS256"
```

**Giải thích:**
- **Environment Configuration**: JWT secret từ environment variable
- **Algorithm Choice**: Sử dụng HS256 (HMAC with SHA-256)
- **Session Integration**: Tích hợp với SessionManager
- **Fallback Secret**: Có secret mặc định cho development

```python
    async def verify_jwt_token(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
        """Verify JWT token with blacklist checking"""
        if not credentials:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        
        token = credentials.credentials
        
        # Check blacklist
        if self.session_manager.is_token_blacklisted(token):
            raise HTTPException(status_code=401, detail="Token has been revoked")
```

**Giải thích:**
- **Credential Validation**: Kiểm tra Authorization header có tồn tại
- **Token Extraction**: Lấy token từ credentials
- **Blacklist Check**: Kiểm tra token có bị blacklist không
- **Security First**: Từ chối token bị revoke ngay lập tức

```python
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Validate expiration
            if datetime.utcnow().timestamp() > payload.get("exp", 0):
                raise jwt.ExpiredSignatureError()
            
            return {
                "user_id": payload.get("user_id"),
                "username": payload.get("username"),
                "role": payload.get("role", "guest"),
                "auth_type": "jwt"
            }
```

**Giải thích:**
- **Token Decoding**: Giải mã JWT với secret và algorithm
- **Expiration Check**: Kiểm tra token có hết hạn không
- **Payload Extraction**: Lấy thông tin user từ payload
- **Default Values**: Cung cấp giá trị mặc định an toàn

```python
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            logger.error(f"JWT authentication failed: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
```

**Giải thích:**
- **Exception Handling**: Xử lý các loại lỗi JWT khác nhau
- **Specific Error Messages**: Thông báo lỗi cụ thể cho từng trường hợp
- **Logging**: Ghi log lỗi để debug
- **Security**: Không expose chi tiết lỗi ra ngoài

### 2. Token Generation

```python
    def generate_jwt_token(self, user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Generate JWT token"""
        try:
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(hours=1)  # Default 1 hour
            
            payload = {
                "user_id": str(user_data.get("_id", user_data.get("user_id"))),
                "username": user_data.get("username"),
                "role": user_data.get("role", "guest"),
                "exp": expire.timestamp(),
                "iat": datetime.utcnow().timestamp(),
                "type": "access"
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            return token
```

**Giải thích:**
- **Flexible Expiration**: Cho phép custom thời gian hết hạn
- **Default Expiration**: Mặc định 1 giờ cho access token
- **Comprehensive Payload**: Bao gồm user_id, username, role, timestamps
- **Token Type**: Đánh dấu loại token (access)
- **ID Handling**: Xử lý cả MongoDB ObjectId và string ID

---

## Session Management

### 1. Refresh Token System

**File: `shared/session_manager.py`**

```python
class SessionManager:
    """Session management with refresh tokens and blacklisting"""
    
    def __init__(self):
        # In-memory blacklist for immediate token invalidation
        # In production, use Redis for distributed systems
        self.blacklisted_tokens: Set[str] = set()
```

**Giải thích:**
- **In-memory Blacklist**: Lưu trữ token bị blacklist trong memory
- **Production Note**: Ghi chú sử dụng Redis cho production
- **Immediate Invalidation**: Vô hiệu hóa token ngay lập tức
- **Set Data Structure**: Sử dụng Set cho lookup nhanh

```python
    async def create_refresh_token(self, user_id: str, device_info: Optional[str] = None, ip_address: Optional[str] = None) -> str:
        """Create new refresh token"""
        try:
            # Generate secure refresh token
            refresh_token = secrets.token_urlsafe(64)
            
            # Set expiration (10 minutes để đủ thời gian user thao tác)
            expires_at = datetime.utcnow() + timedelta(minutes=10)
```

**Giải thích:**
- **Secure Generation**: Sử dụng `secrets.token_urlsafe()` cho bảo mật cao
- **64-byte Token**: Token dài 64 bytes để đảm bảo entropy
- **Short Expiration**: 10 phút để balance security và UX
- **Device Tracking**: Lưu thông tin device và IP

```python
            refresh_tokens_collection = AuthDatabase.get_collection("refresh_tokens")
            
            # First, mark existing tokens as revoked (safer than delete)
            try:
                await refresh_tokens_collection.update_many(
                    {"userId": ObjectId(user_id), "isRevoked": False},
                    {"$set": {"isRevoked": True}}
                )
                logger.info(f"Revoked existing refresh tokens for user {user_id}")
            except Exception as e:
                logger.warning(f"Could not revoke existing tokens for user {user_id}: {e}")
                # Continue anyway - not critical
```

**Giải thích:**
- **Token Revocation**: Vô hiệu hóa token cũ thay vì xóa
- **Data Integrity**: Giữ lại token cũ để audit
- **Error Handling**: Xử lý lỗi nhưng không dừng process
- **Logging**: Ghi log để tracking

```python
            # Create new refresh token record
            token_data = {
                "token": refresh_token,
                "userId": ObjectId(user_id),
                "expiresAt": expires_at,
                "createdAt": datetime.utcnow(),
                "isRevoked": False,
                "deviceInfo": device_info,
                "ipAddress": ip_address
            }
            
            try:
                await refresh_tokens_collection.insert_one(token_data)
                logger.info(f"Created refresh token for user {user_id}, expires at {expires_at}")
            except Exception as e:
                logger.error(f"Failed to insert refresh token: {e}")
                raise Exception(f"Database error creating refresh token: {e}")
            
            return refresh_token
```

**Giải thích:**
- **Complete Token Data**: Lưu đầy đủ thông tin token
- **MongoDB Integration**: Sử dụng ObjectId cho user reference
- **Timestamp Tracking**: Lưu thời gian tạo và hết hạn
- **Device Context**: Lưu thông tin device và IP để security

### 2. HTTP-Only Cookie Implementation

**File: `auth-service/routes/auth_routes.py`**

```python
@router.post("/login")
async def login(login_data: LoginRequest, request: Request, response: Response):
    """Enhanced login with session management"""
    result = await auth_controller.login(login_data, request)
    
    if result.get("success") and result.get("refresh_token"):
        # Set refresh token as HTTP-only cookie
        max_age = 2592000 if login_data.remember_me else 604800  # 30 days or 7 days
        
        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            max_age=max_age,
            httponly=True,  # HTTP-only cookie
            secure=True,    # HTTPS only request
            samesite="strict"  # CSRF protection
        )
        
        # Remove refresh_token from response body
        result.pop("refresh_token", None)
    
    return result
```

**Giải thích:**
- **HTTP-Only Cookie**: Ngăn JavaScript access token
- **Remember Me Logic**: 30 ngày nếu remember, 7 ngày nếu không
- **Security Flags**: Secure cho HTTPS, SameSite cho CSRF protection
- **Response Cleanup**: Xóa refresh_token khỏi response body
- **Environment Aware**: SECURE_COOKIES dựa trên environment

---

## Database Security

### 1. Collection-Level Permissions

**File: `shared/database_security.py`**

```python
COLLECTION_PERMISSIONS = {
    "users": {
        "create": [Permission.CREATE_USERS, Permission.ADMIN_ACCESS],
        "read": [Permission.READ_USERS, Permission.ADMIN_ACCESS],
        "update": [Permission.UPDATE_USERS, Permission.ADMIN_ACCESS],
        "delete": [Permission.DELETE_USERS, Permission.ADMIN_ACCESS]
    },
    "vouchers": {
        "create": [Permission.CREATE_VOUCHERS],
        "read": [Permission.READ_VOUCHERS],  # Public read
        "update": [Permission.UPDATE_VOUCHERS, Permission.UPDATE_OWN_VOUCHERS],
        "delete": [Permission.DELETE_VOUCHERS, Permission.DELETE_OWN_VOUCHERS]
    },
    "carts": {
        "read": [Permission.READ_OWN_CART],
        "update": [Permission.MANAGE_OWN_CART],
        "delete": [Permission.MANAGE_OWN_CART]
    }
}
```

**Giải thích:**
- **Collection Mapping**: Map mỗi collection với CRUD permissions
- **Multiple Permissions**: Một operation có thể có nhiều permission
- **Public vs Private**: Voucher read là public, cart chỉ own
- **Admin Override**: Admin có thể access tất cả

### 2. Data Masking và Row-Level Security

```python
SENSITIVE_FIELDS = {
    "users": ["password", "email", "phone"],
    "sessions": ["token", "refreshToken"],
    "refresh_tokens": ["token"]
}

class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
```

**Giải thích:**
- **Sensitive Fields**: Định nghĩa field cần mask
- **Data Classification**: Phân loại độ nhạy cảm của data
- **Collection-specific**: Mỗi collection có sensitive fields riêng

```python
def apply_row_level_security(self, collection_name: str, data: List[Dict], user_data: Dict[str, Any]) -> List[Dict]:
    """Apply row-level security based on user role and ownership"""
    user_role = self.rbac_manager.get_user_role(user_data)
    user_id = str(user_data.get("user_id", ""))
    
    # Admin và Super Admin có thể xem tất cả
    if user_role in [Role.ADMIN, Role.SUPER_ADMIN]:
        return data
    
    # Filter data based on ownership
    filtered_data = []
    for item in data:
        if self._user_owns_resource(item, user_id, collection_name):
            filtered_data.append(item)
    
    return filtered_data
```

**Giải thích:**
- **Role-based Filtering**: Admin xem tất cả, user chỉ xem của mình
- **Ownership Check**: Kiểm tra user có sở hữu resource không
- **Data Protection**: Bảo vệ data ở mức row
- **Flexible Logic**: Logic có thể customize cho từng collection

---

## Middleware và Decorators

### 1. Permission Decorator

```python
def require_permission(required_permission: Permission):
    """Decorator to require specific permission for endpoint access"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from request context
            user_data = kwargs.get('current_user')
            if not user_data:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Check permission
            rbac_manager = RBACManager()
            if not rbac_manager.has_permission(user_data, required_permission):
                raise HTTPException(
                    status_code=403, 
                    detail=f"Permission denied. Required: {required_permission.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

**Giải thích:**
- **Decorator Pattern**: Wrap function để thêm permission check
- **Authentication Check**: Đảm bảo user đã authenticate
- **Permission Validation**: Kiểm tra user có quyền cần thiết
- **Clear Error Messages**: Thông báo lỗi rõ ràng
- **Function Preservation**: Giữ nguyên metadata của function gốc

### 2. FastAPI Dependencies

```python
async def get_current_user(user: Dict[str, Any] = Depends(auth_middleware.verify_jwt_token)) -> Dict[str, Any]:
    """Get current authenticated user"""
    return user

def require_permission_dep(permission: Permission):
    """FastAPI dependency for permission checking"""
    async def check_permission(current_user: Dict[str, Any] = Depends(get_current_user)):
        rbac_manager = RBACManager()
        if not rbac_manager.has_permission(current_user, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied. Required: {permission.value}"
            )
        return current_user
    return check_permission
```

**Giải thích:**
- **FastAPI Integration**: Sử dụng Depends cho dependency injection
- **Reusable Dependencies**: Có thể tái sử dụng cho nhiều endpoint
- **Chain Dependencies**: get_current_user -> check_permission
- **Type Hints**: Rõ ràng về type để IDE support

---

## Authentication Controller

### 1. User Registration và Login

**File: `auth-service/controllers/auth_controller.py`**

```python
class AuthController:
    """Enhanced JWT-based authentication controller with session management"""
    
    def __init__(self):
        self.auth_db = AuthDatabase()
        self.auth_middleware = AuthMiddleware()
        self.session_manager = SessionManager()
        self.rbac_manager = RBACManager()
        self.jwt_secret = os.getenv("JWT_ACCESS_KEY", "your-secret-key")
```

**Giải thích:**
- **Dependency Injection**: Inject các service cần thiết
- **Single Responsibility**: Mỗi component có trách nhiệm riêng
- **Configuration**: Lấy config từ environment
- **Centralized Logic**: Tập trung logic authentication

```python
async def login(self, login_data: LoginRequest, request: Request) -> Dict[str, Any]:
    """Enhanced JWT-based login with refresh tokens"""
    try:
        # Find user
        user = await self.auth_db.find_user_by_username(login_data.username)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not bcrypt.checkpw(login_data.password.encode('utf-8'), user["password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
```

**Giải thích:**
- **User Lookup**: Tìm user trong database
- **Password Verification**: Sử dụng bcrypt để verify password
- **Security**: Không tiết lộ user có tồn tại hay không
- **Consistent Error**: Cùng error message cho username/password sai

```python
        # Generate access token
        access_token = self.auth_middleware.generate_jwt_token(
            user_data=user,
            expires_delta=timedelta(hours=1)
        )
        
        # Create refresh token
        device_info = request.headers.get("User-Agent", "Unknown")
        ip_address = request.client.host if request.client else "Unknown"
        
        refresh_token = await self.session_manager.create_refresh_token(
            user_id=str(user["_id"]),
            device_info=device_info,
            ip_address=ip_address
        )
```

**Giải thích:**
- **Token Generation**: Tạo access token với thời hạn 1 giờ
- **Device Tracking**: Lưu User-Agent và IP address
- **Session Management**: Tạo refresh token cho session
- **Security Context**: Lưu thông tin để audit và security

```python
        return {
            "success": True,
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": {
                "id": str(user["_id"]),
                "username": user["username"],
                "role": user.get("role", "user")
            },
            "auth_type": "jwt_with_refresh"
        }
```

**Giải thích:**
- **Structured Response**: Response có cấu trúc rõ ràng
- **User Info**: Trả về thông tin user cần thiết
- **Auth Type**: Đánh dấu loại authentication
- **Success Flag**: Boolean để client dễ check

---

## Security Features

### 1. Rate Limiting

```python
class RateLimitMiddleware:
    def __init__(self, calls: int = 100, period: int = 60):
        self.calls = calls
        self.period = period
        self.requests = {}
    
    async def __call__(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old requests
        self.requests = {
            ip: times for ip, times in self.requests.items()
            if any(t > current_time - self.period for t in times)
        }
        
        # Check rate limit
        if client_ip in self.requests:
            if len(self.requests[client_ip]) >= self.calls:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            self.requests[client_ip].append(current_time)
        else:
            self.requests[client_ip] = [current_time]
        
        response = await call_next(request)
        return response
```

**Giải thích:**
- **Sliding Window**: Sử dụng sliding window algorithm
- **IP-based Limiting**: Rate limit dựa trên IP address
- **Memory Cleanup**: Tự động dọn dẹp request cũ
- **Configurable**: Có thể config số request và thời gian
- **HTTP 429**: Trả về status code chuẩn cho rate limit

### 2. Security Headers

```python
class SecurityMiddleware:
    async def __call__(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["X-Session-Security"] = "jwt-authentication-with-refresh"
        
        return response
```

**Giải thích:**
- **Security Headers**: Thêm các header bảo mật chuẩn
- **XSS Protection**: Ngăn chặn XSS attacks
- **Clickjacking Protection**: X-Frame-Options DENY
- **HSTS**: Enforce HTTPS connections
- **CSP**: Content Security Policy để ngăn script injection
- **Custom Header**: Đánh dấu loại authentication system

---

## Kết Luận

Hệ thống authentication và authorization của Voux Microservices được thiết kế với các tính năng bảo mật cao:

### ✅ Điểm Mạnh:
- **JWT Authentication**: Stateless, scalable với PyJWT
- **RBAC System**: Phân quyền chi tiết, dễ mở rộng
- **Session Management**: Refresh tokens với HTTP-only cookies
- **Database Security**: Row-level security và data masking
- **Rate Limiting**: Bảo vệ chống brute force
- **Security Headers**: Comprehensive security headers
- **Token Blacklisting**: Quản lý token revocation
- **Audit Logging**: Ghi log đầy đủ cho security audit

### 🔧 Cải Tiến Có Thể:
- **Redis Integration**: Sử dụng Redis cho distributed blacklist
- **OAuth2 Support**: Thêm OAuth2 cho third-party login
- **2FA Implementation**: Two-factor authentication
- **Advanced Rate Limiting**: Rate limiting dựa trên user/endpoint
- **Security Monitoring**: Real-time security monitoring

### 📚 Best Practices Được Áp Dụng:
- **Principle of Least Privilege**: User chỉ có quyền cần thiết
- **Defense in Depth**: Nhiều lớp bảo mật
- **Secure by Default**: Mặc định secure, opt-in cho permissions
- **Clear Error Messages**: Thông báo lỗi rõ ràng nhưng không expose info
- **Comprehensive Logging**: Log đầy đủ cho audit và debug

Hệ thống đảm bảo tính bảo mật cao while maintaining usability và performance cho ứng dụng microservices.