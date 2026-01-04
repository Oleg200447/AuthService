"""Kafka producer for sending messages."""
import logging
import json
from typing import Any
from aiokafka import AIOKafkaProducer
from app.config import settings

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Async Kafka producer for sending messages."""
    
    def __init__(self):
        self.producer: AIOKafkaProducer | None = None
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
    
    async def start(self):
        """Start the Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                compression_type='gzip',
            )
            await self.producer.start()
            logger.info(f"Kafka producer started: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            self.producer = None
    
    async def stop(self):
        """Stop the Kafka producer."""
        if self.producer:
            try:
                await self.producer.stop()
                logger.info("Kafka producer stopped")
            except Exception as e:
                logger.error(f"Error stopping Kafka producer: {e}")
    
    async def send_message(self, topic: str, message: dict[str, Any]) -> bool:
        """Send a message to a Kafka topic.
        
        Args:
            topic: Kafka topic name
            message: Message dictionary to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self.producer:
            logger.error("Kafka producer not initialized")
            return False
        
        try:
            await self.producer.send_and_wait(topic, value=message)
            logger.info(f"Message sent to Kafka topic '{topic}': {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to Kafka: {e}")
            return False
    
    async def send_new_user_message(
        self,
        user_id: str,
        username: str,
        created_at: str
    ) -> bool:
        """Send new user creation message to Kafka.
        
        Args:
            user_id: User UUID as string
            username: Username
            created_at: Creation timestamp in ISO format
            
        Returns:
            True if successful, False otherwise
        """
        message = {
            "id": user_id,
            "username": username,
            "created_at": created_at
        }
        
        return await self.send_message(settings.KAFKA_TOPIC_NEW_USERS, message)


# Global instance
kafka_producer = KafkaProducer()
