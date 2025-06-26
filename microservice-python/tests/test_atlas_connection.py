#!/usr/bin/env python3
"""
Quick MongoDB Atlas Connection Test

This script quickly tests your Atlas connections without running full security tests.

Usage:
    python test_atlas_connection.py
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from shared.database import Database
from atlas_config import ATLAS_CONFIGS, print_connection_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_single_connection(name: str, uri: str) -> bool:
    """Test a single Atlas connection"""
    try:
        print(f"\n🔗 Testing {name}...")
        
        # Attempt connection
        success = await Database.connect_to_mongo(f"test_{name}", uri)
        
        if success:
            # Test basic operations
            await Database.client.admin.command('ping')
            
            # Get database and test collection operations
            db = Database.get_database(f"test_{name}")
            test_collection = db.connection_test
            
            # Insert test document
            test_doc = {"test": True, "timestamp": datetime.utcnow()}
            result = await test_collection.insert_one(test_doc)
            
            # Verify insertion
            found = await test_collection.find_one({"_id": result.inserted_id})
            
            # Clean up
            await test_collection.delete_one({"_id": result.inserted_id})
            
            if found:
                print(f"✅ {name}: Connection successful - CRUD operations working")
                return True
            else:
                print(f"❌ {name}: Connection failed - CRUD operations not working")
                return False
        else:
            print(f"❌ {name}: Connection failed - Cannot establish connection")
            return False
            
    except Exception as e:
        print(f"❌ {name}: Connection failed - {str(e)}")
        return False

async def test_all_atlas_connections():
    """Test all configured Atlas connections"""
    print("\n" + "="*60)
    print("  MONGODB ATLAS CONNECTION TEST")
    print("="*60)
    
    # Show available connections
    print_connection_info()
    
    print("\n🧪 Testing Connections...")
    print("-" * 40)
    
    results = {}
    
    for config_name, config in ATLAS_CONFIGS.items():
        success = await test_single_connection(config['name'], config['uri'])
        results[config_name] = success
        
    # Print summary
    print("\n" + "="*60)
    print("  CONNECTION TEST SUMMARY")
    print("="*60)
    
    successful_connections = sum(1 for success in results.values() if success)
    total_connections = len(results)
    
    print(f"\n📊 Results: {successful_connections}/{total_connections} connections successful")
    
    for config_name, success in results.items():
        config = ATLAS_CONFIGS[config_name]
        status = "✅" if success else "❌"
        print(f"  {status} {config['name']}")
        
    if successful_connections > 0:
        print("\n🎉 At least one Atlas connection is working!")
        print("\n📋 Next steps:")
        print("   1. Run full security tests: python test_database_security.py")
        print("   2. Run setup script: python setup_atlas_testing.py")
        print("   3. Test API endpoints: python test_security_api.py")
    else:
        print("\n⚠️  No Atlas connections are working.")
        print("\n🔧 Troubleshooting:")
        print("   1. Check your .env file for correct Atlas URIs")
        print("   2. Verify Atlas cluster is running")
        print("   3. Check network access rules in Atlas")
        print("   4. Verify database user permissions")
        
    return results

async def main():
    """Main function"""
    try:
        results = await test_all_atlas_connections()
        
        # Close connections
        if Database.client:
            await Database.close_mongo_connection()
            
        return results
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        print(f"\n❌ Test failed: {e}")
        return {}

if __name__ == "__main__":
    asyncio.run(main())