#!/usr/bin/env python3
"""
Debug RabbitMQ Connection
"""

import asyncio
import sys
import os

def test_import():
    """Test if aio-pika can be imported"""
    try:
        import aio_pika
        print("✅ aio-pika import successful")
        print(f"aio-pika version: {aio_pika.__version__}")
        return True
    except ImportError as e:
        print(f"❌ aio-pika import failed: {e}")
        print("💡 Run: pip install aio-pika==9.4.0")
        return False

async def test_connection():
    """Test RabbitMQ connection"""
    try:
        import aio_pika
        
        # Test different connection URLs
        test_urls = [
            "amqp://admin:password@localhost:5672/",
            "amqp://guest:guest@localhost:5672/",
            "amqp://localhost:5672/"
        ]
        
        for url in test_urls:
            print(f"\n🔗 Testing connection: {url}")
            
            try:
                connection = await aio_pika.connect_robust(url, timeout=5)
                print(f"✅ Connection successful: {url}")
                
                # Test channel
                channel = await connection.channel()
                print("✅ Channel created successfully")
                
                # Test exchange
                exchange = await channel.declare_exchange(
                    "test_exchange",
                    aio_pika.ExchangeType.TOPIC,
                    durable=True
                )
                print("✅ Exchange declared successfully")
                
                await connection.close()
                print("✅ Connection closed cleanly")
                return True
                
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                continue
        
        print("❌ All connection attempts failed")
        return False
        
    except ImportError:
        print("❌ aio-pika not available")
        return False

async def main():
    """Main debug function"""
    print("🐰 RabbitMQ Connection Debug")
    print("=" * 50)
    
    # Test 1: Import
    if not test_import():
        return
    
    # Test 2: Connection
    await test_connection()
    
    print("\n" + "=" * 50)
    print("🏁 Debug completed!")

if __name__ == "__main__":
    asyncio.run(main()) 