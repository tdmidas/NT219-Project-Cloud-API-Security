#!/usr/bin/env python3
"""
MongoDB Atlas Setup and Testing Script

This script helps you:
1. Configure MongoDB Atlas connections
2. Test Atlas connectivity
3. Run database security tests with Atlas
4. Migrate from localhost to Atlas

Usage:
    python setup_atlas_testing.py
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from shared.database import Database
from atlas_config import ATLAS_CONFIGS, get_atlas_connection_string, print_connection_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AtlasSetupManager:
    """Manage Atlas setup and testing"""
    
    def __init__(self):
        self.test_results = {}
        
    def print_header(self, title: str):
        """Print formatted header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        
    def print_step(self, step: str, description: str):
        """Print formatted step"""
        print(f"\n🔸 Step {step}: {description}")
        print("-" * 40)
        
    async def test_connection(self, config_name: str, uri: str) -> bool:
        """Test a single Atlas connection"""
        try:
            logger.info(f"Testing {config_name} connection...")
            success = await Database.connect_to_mongo(f"test_{config_name}", uri)
            
            if success:
                # Test basic operations
                db = Database.get_database(f"test_{config_name}")
                
                # Test ping
                await Database.client.admin.command('ping')
                
                # Test collection operations
                test_collection = db.test_connection
                test_doc = {"test": True, "timestamp": datetime.utcnow()}
                
                # Insert test document
                result = await test_collection.insert_one(test_doc)
                
                # Find test document
                found_doc = await test_collection.find_one({"_id": result.inserted_id})
                
                # Clean up test document
                await test_collection.delete_one({"_id": result.inserted_id})
                
                if found_doc:
                    logger.info(f"✅ {config_name} connection successful - Full CRUD operations working")
                    return True
                else:
                    logger.error(f"❌ {config_name} connection failed - CRUD operations not working")
                    return False
                    
            else:
                logger.error(f"❌ {config_name} connection failed - Cannot connect")
                return False
                
        except Exception as e:
            logger.error(f"❌ {config_name} connection failed: {e}")
            return False
            
    async def test_all_connections(self):
        """Test all configured Atlas connections"""
        self.print_step("1", "Testing All Atlas Connections")
        
        results = {}
        
        for config_name, config in ATLAS_CONFIGS.items():
            print(f"\n🔗 Testing {config['name']}...")
            success = await self.test_connection(config_name, config['uri'])
            results[config_name] = {
                "name": config['name'],
                "success": success,
                "uri_preview": config['uri'][:50] + "..."
            }
            
        self.test_results['connections'] = results
        return results
        
    def check_environment_variables(self):
        """Check if Atlas environment variables are set"""
        self.print_step("2", "Checking Environment Variables")
        
        env_vars = [
            "AUTH_DB_URI",
            "USER_DB_URI", 
            "VOUCHER_DB_URI",
            "CART_DB_URI"
        ]
        
        env_status = {}
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                is_atlas = "mongodb+srv://" in value
                env_status[var] = {
                    "set": True,
                    "is_atlas": is_atlas,
                    "preview": value[:50] + "..." if len(value) > 50 else value
                }
                status_icon = "🌐" if is_atlas else "🏠"
                db_type = "Atlas" if is_atlas else "Local"
                print(f"  {status_icon} {var}: {db_type} - {value[:50]}...")
            else:
                env_status[var] = {"set": False, "is_atlas": False, "preview": "Not set"}
                print(f"  ❌ {var}: Not set")
                
        self.test_results['environment'] = env_status
        return env_status
        
    async def run_security_tests(self):
        """Run database security tests with Atlas"""
        self.print_step("3", "Running Database Security Tests")
        
        try:
            # Import and run the security tests
            from test_database_security import DatabaseSecurityTester
            
            print("\n🧪 Starting comprehensive security tests...")
            tester = DatabaseSecurityTester()
            
            # Setup with Atlas
            await tester.setup()
            
            # Run all tests
            await tester.run_all_tests()
            
            # Generate report
            report = await tester.generate_report()
            
            print("\n✅ Security tests completed successfully!")
            print(f"📊 Test results saved to: {report['report_file']}")
            
            self.test_results['security_tests'] = {
                "success": True,
                "report_file": report['report_file'],
                "summary": report['summary']
            }
            
        except Exception as e:
            logger.error(f"Security tests failed: {e}")
            self.test_results['security_tests'] = {
                "success": False,
                "error": str(e)
            }
            
    def generate_setup_report(self):
        """Generate comprehensive setup report"""
        self.print_step("4", "Generating Setup Report")
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "atlas_setup_results": self.test_results
        }
        
        # Save to file
        report_file = f"atlas_setup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        print(f"\n📋 Setup report saved to: {report_file}")
        
        # Print summary
        self.print_summary()
        
        return report_file
        
    def print_summary(self):
        """Print setup summary"""
        print("\n" + "="*60)
        print("  ATLAS SETUP SUMMARY")
        print("="*60)
        
        # Connection results
        if 'connections' in self.test_results:
            print("\n🔗 Connection Test Results:")
            for name, result in self.test_results['connections'].items():
                status = "✅" if result['success'] else "❌"
                print(f"  {status} {result['name']}")
                
        # Environment variables
        if 'environment' in self.test_results:
            print("\n🌍 Environment Variables:")
            atlas_count = sum(1 for env in self.test_results['environment'].values() if env.get('is_atlas', False))
            total_count = len(self.test_results['environment'])
            print(f"  📊 Atlas URIs: {atlas_count}/{total_count}")
            
        # Security tests
        if 'security_tests' in self.test_results:
            security_status = "✅" if self.test_results['security_tests']['success'] else "❌"
            print(f"\n🛡️  Security Tests: {security_status}")
            
        print("\n🎉 Atlas setup process completed!")
        
    def print_next_steps(self):
        """Print recommended next steps"""
        print("\n" + "="*60)
        print("  RECOMMENDED NEXT STEPS")
        print("="*60)
        
        print("\n1. 🧪 Run Individual Test Scripts:")
        print("   python test_database_security.py")
        print("   python quick_security_demo.py")
        print("   python test_security_api.py")
        
        print("\n2. 🔧 Update Your Services:")
        print("   - Update .env files with Atlas URIs")
        print("   - Restart your microservices")
        print("   - Test API endpoints")
        
        print("\n3. 📚 Documentation:")
        print("   - Read DATABASE_SECURITY_TESTING_GUIDE.md")
        print("   - Check API_TESTING_GUIDE.md")
        
        print("\n4. 🚀 Production Deployment:")
        print("   - Set up Atlas network access rules")
        print("   - Configure Atlas authentication")
        print("   - Enable Atlas monitoring")
        
async def main():
    """Main setup process"""
    manager = AtlasSetupManager()
    
    manager.print_header("MongoDB Atlas Setup & Testing")
    
    print("\n🎯 This script will:")
    print("   1. Test Atlas connections")
    print("   2. Check environment variables")
    print("   3. Run security tests")
    print("   4. Generate setup report")
    
    # Show available connections
    print_connection_info()
    
    try:
        # Step 1: Test connections
        await manager.test_all_connections()
        
        # Step 2: Check environment
        manager.check_environment_variables()
        
        # Step 3: Run security tests
        await manager.run_security_tests()
        
        # Step 4: Generate report
        manager.generate_setup_report()
        
        # Show next steps
        manager.print_next_steps()
        
    except Exception as e:
        logger.error(f"Setup process failed: {e}")
        print(f"\n❌ Setup failed: {e}")
        
    finally:
        # Close database connections
        if Database.client:
            await Database.close_mongo_connection()
            
if __name__ == "__main__":
    asyncio.run(main())