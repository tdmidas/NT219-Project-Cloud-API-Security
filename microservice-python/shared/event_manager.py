import asyncio
import json
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import aio_pika
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue
import os

logger = logging.getLogger(__name__)

class EventManager:
    """Event-driven communication manager using RabbitMQ"""
    
    def __init__(self):
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.exchange = None
        self.rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://admin:password@localhost:5672/")
        
    async def connect(self):
        """Connect to RabbitMQ"""
        try:
            # Add timeout to prevent hanging
            self.connection = await asyncio.wait_for(
                aio_pika.connect_robust(self.rabbitmq_url),
                timeout=10.0  # 10 second timeout
            )
            self.channel = await self.connection.channel()
            
            # Declare exchange for user events
            self.exchange = await self.channel.declare_exchange(
                "user_events", 
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            logger.info("✅ Connected to RabbitMQ successfully")
            return True
            
        except asyncio.TimeoutError:
            logger.error("❌ RabbitMQ connection timeout (10s)")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("🔌 Disconnected from RabbitMQ")
    
    async def publish_event(self, event_type: str, event_data: Dict[str, Any]):
        """Publish event to RabbitMQ"""
        try:
            if not self.exchange:
                await self.connect()
            
            # Prepare event message
            message_body = {
                "event_type": event_type,
                "event_data": event_data,
                "timestamp": datetime.utcnow().isoformat(),
                "source_service": "auth-service"
            }
            
            message = aio_pika.Message(
                json.dumps(message_body).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            # Publish to exchange with routing key
            await self.exchange.publish(message, routing_key=event_type)
            
            logger.info(f"📤 Published event: {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish event {event_type}: {e}")
            return False
    
    async def consume_events(self, queue_name: str, routing_keys: list, callback: Callable):
        """Consume events from RabbitMQ"""
        try:
            if not self.channel:
                success = await self.connect()
                if not success:
                    logger.error("❌ Cannot start consumer - no RabbitMQ connection")
                    return
            
            # Declare queue with shorter message TTL to prevent buildup
            queue = await self.channel.declare_queue(
                queue_name, 
                durable=True,
                auto_delete=False
            )
            
            # Bind queue to exchange with routing keys
            for routing_key in routing_keys:
                await queue.bind(self.exchange, routing_key=routing_key)
            
            # Set up consumer with better error handling
            async def message_handler(message: aio_pika.IncomingMessage):
                try:
                    async with message.process():
                        # Parse message
                        body = json.loads(message.body.decode())
                        
                        logger.info(f"📥 Received event: {body.get('event_type')}")
                        
                        # Call callback function with timeout
                        await asyncio.wait_for(callback(body), timeout=30.0)
                        
                except asyncio.TimeoutError:
                    logger.error(f"⏰ Message processing timeout for event: {body.get('event_type', 'unknown')}")
                    # Message will be requeued
                    raise
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Invalid JSON in message: {e}")
                    # Don't requeue invalid JSON
                    return
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    # Message will be requeued due to exception
                    raise
            
            # Start consuming with QoS settings
            await self.channel.set_qos(prefetch_count=1)  # Process one message at a time
            await queue.consume(message_handler)
            
            logger.info(f"👂 Started consuming events on queue: {queue_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup consumer: {e}")
            raise

# Singleton instance
event_manager = EventManager() 