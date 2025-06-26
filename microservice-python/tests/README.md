# Voux Microservices - Python Edition

🐍 A complete migration of the Voux microservices architecture from Node.js to Python using FastAPI.

## 📁 Project Structure

```
microservice-python/
├── shared/                          # Shared components
│   ├── models/                      # Pydantic models
│   │   └── user.py                 # User model with validation
│   ├── database.py                 # Database connections
│   └── middleware.py               # Authentication & security middleware
├── auth-service/                   # Authentication service
│   ├── controllers/
│   │   └── auth_controller.py      # Authentication logic
│   ├── routes/
│   │   └── auth_routes.py          # Auth API endpoints
│   ├── main.py                     # FastAPI app
│   └── Dockerfile
├── user-service/                   # User management service
├── voucher-service/                # Voucher CRUD service
├── cart-service/                   # Shopping cart service
├── api-gateway/                    # API Gateway
├── requirements.txt                # Python dependencies
├── docker-compose.yml              # Docker orchestration
├── start-all-services.py           # Service launcher script
└── README.md                       # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip
- MongoDB (local or Docker)
- Redis (for session storage)
- Docker & Docker Compose (optional)

### Installation

1. **Clone and navigate to Python microservices:**
   ```bash
   cd microservice-python
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configurations
   ```

4. **Start all services:**
   ```bash
   python start-all-services.py --dev --wait
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
# Database
AUTH_DB_URI=mongodb://localhost:27017/voux_auth
USER_DB_URI=mongodb://localhost:27017/voux_users
VOUCHER_DB_URI=mongodb://localhost:27017/voux_vouchers
CART_DB_URI=mongodb://localhost:27017/voux_cart

# Security
JWT_ACCESS_KEY=your-super-secret-jwt-key

# Services
AUTH_SERVICE_PORT=3001
USER_SERVICE_PORT=3002
VOUCHER_SERVICE_PORT=3003
CART_SERVICE_PORT=3004
API_GATEWAY_PORT=8000

# Frontend
FRONTEND_URL=http://localhost:5173

# Redis
REDIS_URL=redis://localhost:6379
```

## 🏗️ Service Architecture

### Core Services

| Service             | Port | Purpose                                           | Technology                 |
| ------------------- | ---- | ------------------------------------------------- | -------------------------- |
| **Auth Service**    | 3001 | Authentication, Authorization, Session Management | FastAPI + PyMongo + JWT    |
| **User Service**    | 3002 | User profile management                           | FastAPI + PyMongo          |
| **Voucher Service** | 3003 | Voucher CRUD operations                           | FastAPI + PyMongo + Celery |
| **Cart Service**    | 3004 | Shopping cart functionality                       | FastAPI + PyMongo          |
| **API Gateway**     | 8000 | Request routing, load balancing                   | FastAPI + httpx            |

### Key Features

#### 🔐 Enhanced Security
- **JWT Authentication**: Standard JSON Web Token authentication
- **Session Management**: JWT-based session tokens
- **Rate Limiting**: Request throttling per IP
- **RBAC**: Role-based access control

#### 📊 Database Design
- **MongoDB**: Document-based storage
- **Motor**: Async MongoDB driver
- **Connection Pooling**: Optimized database connections
- **Health Monitoring**: Database status checks

## 🛠️ Development

### Running Individual Services

```bash
# Start auth service in development mode
cd auth-service
uvicorn main:app --reload --port 3001

# Start user service
cd user-service
uvicorn main:app --reload --port 3002

# Start specific services only
python start-all-services.py --services auth-service user-service --dev
```

### API Documentation

Each service provides interactive API documentation:

- Auth Service: http://localhost:3001/docs
- User Service: http://localhost:3002/docs
- Voucher Service: http://localhost:3003/docs
- Cart Service: http://localhost:3004/docs
- API Gateway: http://localhost:8000/docs

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f [service-name]
```

### Environment Setup for Docker

```bash
# Create production environment file
cp .env.example .env.docker

# Update with production values
vim .env.docker

# Use with docker-compose
docker-compose --env-file .env.docker up
```

## 🔄 Migration from Node.js

### What's Been Migrated

✅ **Complete Features:**
- JWT Authentication system
- User management and profiles
- Database models and connections
- Security middleware and RBAC
- Rate limiting and audit logging
- Docker containerization

✅ **Enhanced Features:**
- Type safety with Pydantic
- Async/await throughout
- Better error handling
- Comprehensive API documentation
- Health checks and monitoring

### Key Differences from Node.js Version

| Aspect             | Node.js               | Python              |
| ------------------ | --------------------- | ------------------- |
| **Framework**      | Express.js            | FastAPI             |
| **Type System**    | TypeScript (optional) | Pydantic (built-in) |
| **Database**       | Mongoose              | Motor + PyMongo     |
| **Validation**     | Custom middleware     | Pydantic models     |
| **Documentation**  | Manual/Swagger        | Auto-generated      |
| **Testing**        | Jest                  | Pytest              |
| **Authentication** | JWT                   | JWT                 |

## 📋 API Reference

### Authentication Endpoints

```http
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
POST /api/auth/refresh
GET  /api/auth/profile
```

### User Endpoints

```http
GET    /api/users/
GET    /api/users/profile/me
PUT    /api/users/profile/me
DELETE /api/users/{id}
```

### Voucher Endpoints

```http
GET    /api/vouchers/getAllVoucher
POST   /api/vouchers/createVoucher
GET    /api/vouchers/search
GET    /api/vouchers/categories
```

## 🧪 Security Features

### JWT Authentication

1. **Login**: User provides credentials
2. **Token Generation**: Server generates JWT token
3. **Token Usage**: Client includes token in Authorization header
4. **Token Verification**: Server validates token on each request
5. **Token Refresh**: Refresh tokens for extended sessions

### Session Management

- JWT tokens with configurable expiration
- Token refresh mechanism
- Automatic token validation
- Role-based access control

## 📈 Performance

### Optimizations

- **Async Operations**: Non-blocking I/O throughout
- **Connection Pooling**: Efficient database connections
- **Caching**: Redis for session storage
- **Rate Limiting**: Prevent abuse and ensure stability

### Monitoring

- Health check endpoints for all services
- Request logging and audit trails
- Error tracking and reporting
- Performance metrics collection

## 🔧 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port
   lsof -i :3001
   
   # Kill process
   kill -9 <PID>
   ```

2. **Database Connection Failed**
   ```bash
   # Check MongoDB status
   brew services list | grep mongodb
   
   # Start MongoDB
   brew services start mongodb/brew/mongodb-community
   ```

3. **Dependencies Missing**
   ```bash
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   ```

4. **JWT Token Issues**
   ```bash
   # Check JWT secret configuration
   echo $JWT_ACCESS_KEY
   
   # Update .env file with proper JWT secret
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

### Code Style

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI framework for excellent async support
- Pydantic for robust data validation
- Motor for async MongoDB operations
- PyJWT for JWT authentication
- Original Node.js implementation as migration reference

---

**🔥 Ready to scale with Python's power and FastAPI's speed!** 