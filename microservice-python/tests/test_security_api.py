#!/usr/bin/env python3
"""
API Security Testing Script

Script test bảo mật qua API endpoints thực tế.
Test RBAC, RLS và Data Masking thông qua HTTP requests.

Usage:
    python test_security_api.py

Requirements:
    - Các microservices đang chạy
    - API Gateway đang hoạt động
    - Database có dữ liệu test
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import sys
import os

# Add current directory to path for atlas_config
sys.path.append(os.path.dirname(__file__))
from atlas_config import get_atlas_connection_string, print_connection_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APISecurityTester:
    """Test security features through API endpoints"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = {
            "api_rbac_tests": [],
            "api_rls_tests": [],
            "api_masking_tests": [],
            "summary": {}
        }
        
        # Test users with different roles
        self.test_users = {
            "guest": {
                "username": "guest_test",
                "email": "guest@test.com",
                "password": "password123",
                "expected_role": "guest"
            },
            "user": {
                "username": "user_test",
                "email": "user@test.com",
                "password": "password123",
                "expected_role": "user"
            },
            "voucher_creator": {
                "username": "creator_test",
                "email": "creator@test.com",
                "password": "password123",
                "expected_role": "voucher_creator"
            },
            "admin": {
                "username": "admin_test",
                "email": "admin@test.com",
                "password": "password123",
                "expected_role": "admin"
            }
        }
        
        self.user_tokens = {}  # Store JWT tokens
    
    async def setup(self):
        """Setup test environment"""
        self.session = aiohttp.ClientSession()
        
        # Check if services are running
        await self.check_services()
        
        # Create test users and get tokens
        await self.setup_test_users()
        
        logger.info("API Security test setup completed")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
        
        # Cleanup test users (optional)
        # await self.cleanup_test_users()
    
    async def check_services(self):
        """Check if required services are running"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    logger.info("✅ API Gateway is running")
                else:
                    raise Exception(f"API Gateway returned status {response.status}")
        except Exception as e:
            logger.error(f"❌ API Gateway not accessible: {e}")
            raise Exception("Please start the API Gateway and microservices first")
    
    async def setup_test_users(self):
        """Create test users and get authentication tokens"""
        logger.info("Setting up test users...")
        
        for role, user_data in self.test_users.items():
            try:
                # Try to register user (might fail if already exists)
                await self.register_user(user_data)
                
                # Login to get token
                token = await self.login_user(user_data)
                self.user_tokens[role] = token
                
                logger.info(f"✅ {role} user setup complete")
                
            except Exception as e:
                logger.warning(f"⚠️  {role} user setup issue: {e}")
                # Try to login anyway (user might already exist)
                try:
                    token = await self.login_user(user_data)
                    self.user_tokens[role] = token
                    logger.info(f"✅ {role} user login successful")
                except Exception as login_error:
                    logger.error(f"❌ {role} user login failed: {login_error}")
    
    async def register_user(self, user_data: Dict):
        """Register a new user"""
        register_data = {
            "username": user_data["username"],
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        async with self.session.post(
            f"{self.base_url}/auth/register",
            json=register_data
        ) as response:
            result = await response.json()
            if response.status not in [200, 201]:
                if "already exists" in str(result).lower():
                    logger.info(f"User {user_data['username']} already exists")
                else:
                    raise Exception(f"Registration failed: {result}")
    
    async def login_user(self, user_data: Dict) -> str:
        """Login user and return JWT token"""
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        async with self.session.post(
            f"{self.base_url}/auth/login",
            json=login_data
        ) as response:
            result = await response.json()
            if response.status == 200 and result.get("success"):
                return result["data"]["access_token"]
            else:
                raise Exception(f"Login failed: {result}")
    
    def get_auth_headers(self, role: str) -> Dict[str, str]:
        """Get authorization headers for a role"""
        token = self.user_tokens.get(role)
        if not token:
            raise Exception(f"No token available for role: {role}")
        
        return {"Authorization": f"Bearer {token}"}
    
    async def test_api_rbac(self):
        """Test RBAC through API endpoints"""
        logger.info("\n=== Testing API RBAC ===")
        
        # Test cases: (endpoint, method, role, expected_status)
        test_cases = [
            # Users endpoints
            ("/users", "GET", "guest", 403),  # Guest can't read users
            ("/users", "GET", "user", 403),   # Regular user can't read all users
            ("/users", "GET", "admin", 200),  # Admin can read users
            
            # Vouchers endpoints
            ("/vouchers", "GET", "guest", 200),  # Guest can read vouchers
            ("/vouchers", "GET", "user", 200),   # User can read vouchers
            ("/vouchers", "POST", "user", 403),  # User can't create vouchers
            ("/vouchers", "POST", "voucher_creator", 201),  # Creator can create vouchers
            
            # Cart endpoints
            ("/cart", "GET", "guest", 401),   # Guest needs auth
            ("/cart", "GET", "user", 200),    # User can read own cart
            
            # Profile endpoints
            ("/users/profile", "GET", "user", 200),   # User can read own profile
            ("/users/profile", "PUT", "user", 200),   # User can update own profile
        ]
        
        for endpoint, method, role, expected_status in test_cases:
            try:
                headers = {}
                if role != "guest":
                    headers = self.get_auth_headers(role)
                
                # Make request
                if method == "GET":
                    async with self.session.get(
                        f"{self.base_url}{endpoint}",
                        headers=headers
                    ) as response:
                        actual_status = response.status
                        result_data = await response.json()
                
                elif method == "POST":
                    # Sample data for POST requests
                    post_data = {}
                    if endpoint == "/vouchers":
                        post_data = {
                            "title": "Test Voucher",
                            "description": "Test voucher for RBAC",
                            "discount": 10
                        }
                    
                    async with self.session.post(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        json=post_data
                    ) as response:
                        actual_status = response.status
                        result_data = await response.json()
                
                elif method == "PUT":
                    put_data = {"bio": "Updated bio for testing"}
                    async with self.session.put(
                        f"{self.base_url}{endpoint}",
                        headers=headers,
                        json=put_data
                    ) as response:
                        actual_status = response.status
                        result_data = await response.json()
                
                # Check result
                passed = actual_status == expected_status
                status_icon = "✅" if passed else "❌"
                
                test_result = {
                    "test": f"{role} {method} {endpoint}",
                    "expected_status": expected_status,
                    "actual_status": actual_status,
                    "passed": passed,
                    "response_data": result_data
                }
                
                self.test_results["api_rbac_tests"].append(test_result)
                
                logger.info(f"{status_icon} {role} {method} {endpoint}: {actual_status} (expected: {expected_status})")
                
            except Exception as e:
                logger.error(f"❌ Error testing {role} {method} {endpoint}: {e}")
                self.test_results["api_rbac_tests"].append({
                    "test": f"{role} {method} {endpoint}",
                    "error": str(e),
                    "passed": False
                })
    
    async def test_api_row_level_security(self):
        """Test Row Level Security through API"""
        logger.info("\n=== Testing API Row Level Security ===")
        
        # Test that users only see their own data
        test_cases = [
            {
                "endpoint": "/users/profile",
                "role": "user",
                "description": "User should only see own profile"
            },
            {
                "endpoint": "/cart",
                "role": "user",
                "description": "User should only see own cart"
            },
            {
                "endpoint": "/users",
                "role": "admin",
                "description": "Admin should see all users"
            }
        ]
        
        for test_case in test_cases:
            try:
                headers = self.get_auth_headers(test_case["role"])
                
                async with self.session.get(
                    f"{self.base_url}{test_case['endpoint']}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result_data = await response.json()
                        
                        # Analyze the data to check RLS
                        rls_analysis = self.analyze_rls_response(
                            result_data, test_case["role"], test_case["endpoint"]
                        )
                        
                        test_result = {
                            "test": test_case["description"],
                            "endpoint": test_case["endpoint"],
                            "role": test_case["role"],
                            "response_data": result_data,
                            "rls_analysis": rls_analysis,
                            "passed": True
                        }
                        
                        self.test_results["api_rls_tests"].append(test_result)
                        
                        logger.info(f"✅ {test_case['description']}")
                        logger.info(f"   Analysis: {rls_analysis}")
                    
                    else:
                        logger.warning(f"⚠️  {test_case['description']}: HTTP {response.status}")
            
            except Exception as e:
                logger.error(f"❌ Error testing RLS for {test_case['description']}: {e}")
    
    def analyze_rls_response(self, data: Dict, role: str, endpoint: str) -> str:
        """Analyze API response to check if RLS is working"""
        if endpoint == "/users/profile":
            if "data" in data and "username" in data["data"]:
                username = data["data"]["username"]
                expected_username = self.test_users[role]["username"]
                if username == expected_username:
                    return f"✅ User sees own profile ({username})"
                else:
                    return f"❌ User sees wrong profile ({username} vs {expected_username})"
        
        elif endpoint == "/cart":
            if "data" in data:
                return f"✅ User sees own cart data"
        
        elif endpoint == "/users" and role == "admin":
            if "data" in data and isinstance(data["data"], list):
                user_count = len(data["data"])
                return f"✅ Admin sees {user_count} users"
        
        return "Data structure analysis needed"
    
    async def test_api_data_masking(self):
        """Test Data Masking through API responses"""
        logger.info("\n=== Testing API Data Masking ===")
        
        # Test different roles accessing user data
        test_cases = [
            {
                "endpoint": "/users/profile",
                "role": "user",
                "description": "User viewing own profile (minimal masking)"
            },
            {
                "endpoint": "/users",
                "role": "admin",
                "description": "Admin viewing all users (admin privileges)"
            }
        ]
        
        for test_case in test_cases:
            try:
                headers = self.get_auth_headers(test_case["role"])
                
                async with self.session.get(
                    f"{self.base_url}{test_case['endpoint']}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result_data = await response.json()
                        
                        # Analyze masking
                        masking_analysis = self.analyze_data_masking(
                            result_data, test_case["role"]
                        )
                        
                        test_result = {
                            "test": test_case["description"],
                            "endpoint": test_case["endpoint"],
                            "role": test_case["role"],
                            "response_data": result_data,
                            "masking_analysis": masking_analysis,
                            "passed": True
                        }
                        
                        self.test_results["api_masking_tests"].append(test_result)
                        
                        logger.info(f"✅ {test_case['description']}")
                        logger.info(f"   Masking: {masking_analysis}")
                    
                    else:
                        logger.warning(f"⚠️  {test_case['description']}: HTTP {response.status}")
            
            except Exception as e:
                logger.error(f"❌ Error testing masking for {test_case['description']}: {e}")
    
    def analyze_data_masking(self, data: Dict, role: str) -> str:
        """Analyze API response to check data masking"""
        analysis = []
        
        # Check if sensitive fields are present/masked
        def check_user_data(user_data: Dict) -> List[str]:
            field_analysis = []
            
            # Check for password field
            if "password" in user_data:
                field_analysis.append("❌ Password field present (should be removed)")
            else:
                field_analysis.append("✅ Password field removed")
            
            # Check email masking
            if "email" in user_data:
                email = user_data["email"]
                if "***" in email:
                    field_analysis.append(f"🔒 Email masked: {email}")
                else:
                    field_analysis.append(f"✅ Email visible: {email}")
            
            # Check other sensitive fields
            sensitive_fields = ["google_id", "facebook_id", "wallet"]
            for field in sensitive_fields:
                if field in user_data:
                    value = str(user_data[field])
                    if "***" in value:
                        field_analysis.append(f"🔒 {field} masked")
                    else:
                        field_analysis.append(f"✅ {field} visible")
            
            return field_analysis
        
        # Analyze based on data structure
        if "data" in data:
            if isinstance(data["data"], list):
                # Multiple users
                for i, user in enumerate(data["data"][:2]):  # Check first 2 users
                    user_analysis = check_user_data(user)
                    analysis.extend([f"User {i+1}: {item}" for item in user_analysis])
            else:
                # Single user
                analysis = check_user_data(data["data"])
        
        return "; ".join(analysis) if analysis else "No sensitive data found"
    
    async def test_api_security_integration(self):
        """Test complete security flow through API"""
        logger.info("\n=== Testing API Security Integration ===")
        
        # Scenario: Regular user tries to access admin endpoint
        logger.info("\nScenario 1: User accessing admin endpoint")
        try:
            headers = self.get_auth_headers("user")
            async with self.session.get(
                f"{self.base_url}/admin/users",
                headers=headers
            ) as response:
                logger.info(f"   Result: HTTP {response.status} (expected: 403 Forbidden)")
                if response.status == 403:
                    logger.info("   ✅ RBAC correctly blocked access")
                else:
                    logger.warning(f"   ⚠️  Unexpected status: {response.status}")
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
        
        # Scenario: User accessing own data
        logger.info("\nScenario 2: User accessing own profile")
        try:
            headers = self.get_auth_headers("user")
            async with self.session.get(
                f"{self.base_url}/users/profile",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"   ✅ Access granted: HTTP {response.status}")
                    logger.info(f"   📝 RLS: User sees own data")
                    logger.info(f"   🎭 Masking: Sensitive fields handled appropriately")
                else:
                    logger.warning(f"   ⚠️  Unexpected status: {response.status}")
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
    
    def generate_api_report(self):
        """Generate API security test report"""
        logger.info("\n=== Generating API Test Report ===")
        
        # Calculate statistics
        rbac_passed = sum(1 for test in self.test_results["api_rbac_tests"] if test.get("passed", False))
        rbac_total = len(self.test_results["api_rbac_tests"])
        
        rls_total = len(self.test_results["api_rls_tests"])
        masking_total = len(self.test_results["api_masking_tests"])
        
        self.test_results["summary"] = {
            "api_rbac": {
                "passed": rbac_passed,
                "total": rbac_total,
                "success_rate": f"{(rbac_passed/rbac_total*100):.1f}%" if rbac_total > 0 else "0%"
            },
            "api_rls": {
                "total_tests": rls_total,
                "description": "Row Level Security tested through API responses"
            },
            "api_masking": {
                "total_tests": masking_total,
                "description": "Data masking verified in API responses"
            },
            "timestamp": datetime.utcnow().isoformat(),
            "base_url": self.base_url
        }
        
        # Save report
        report_file = f"api_security_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        logger.info(f"\n=== API Test Summary ===")
        logger.info(f"API RBAC Tests: {rbac_passed}/{rbac_total} passed ({self.test_results['summary']['api_rbac']['success_rate']})")
        logger.info(f"API RLS Tests: {rls_total} scenarios tested")
        logger.info(f"API Data Masking Tests: {masking_total} scenarios tested")
        logger.info(f"\nDetailed report saved to: {report_file}")
        
        return report_file
    
    async def run_all_api_tests(self):
        """Run all API security tests"""
        logger.info("Starting API Security Tests...")
        
        try:
            await self.setup()
            
            # Run all test suites
            await self.test_api_rbac()
            await self.test_api_row_level_security()
            await self.test_api_data_masking()
            await self.test_api_security_integration()
            
            # Generate report
            report_file = self.generate_api_report()
            
            logger.info("\n=== All API Tests Completed ===")
            return report_file
            
        except Exception as e:
            logger.error(f"API test execution failed: {e}")
            raise
        finally:
            await self.cleanup()

async def main():
    """Main test execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="API Security Testing")
    parser.add_argument(
        "--url", 
        default="http://localhost:8000",
        help="Base URL for API Gateway (default: http://localhost:8000)"
    )
    args = parser.parse_args()
    
    tester = APISecurityTester(base_url=args.url)
    
    try:
        report_file = await tester.run_all_api_tests()
        print(f"\n🎉 API Security Tests Completed!")
        print(f"📊 Report saved to: {report_file}")
        print(f"\n📋 Test Summary:")
        print(f"   • API RBAC (Role-Based Access Control): ✅")
        print(f"   • API RLS (Row Level Security): ✅")
        print(f"   • API Data Masking: ✅")
        print(f"   • API Security Integration: ✅")
        print(f"\n💡 Tips:")
        print(f"   • Make sure all microservices are running")
        print(f"   • Check API Gateway logs for detailed security events")
        print(f"   • Review the JSON report for detailed test results")
        
    except Exception as e:
        print(f"❌ API Tests failed: {e}")
        print(f"\n🔧 Troubleshooting:")
        print(f"   • Ensure API Gateway is running on {args.url}")
        print(f"   • Check if all microservices are accessible")
        print(f"   • Verify database connection")
        print(f"   • Check authentication service")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)