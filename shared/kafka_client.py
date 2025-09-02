from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import json
import logging
import os
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)

class KafkaClient:
    def __init__(self):
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
        self.producer = None
        self.consumer = None
    
    def get_producer(self):
        """Get Kafka producer instance"""
        if not self.producer:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                retry_backoff_ms=1000
            )
        return self.producer
    
    def get_consumer(self, topics: list, group_id: str):
        """Get Kafka consumer instance"""
        return KafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )
    
    def send_message(self, topic: str, message: Dict[Any, Any], key: str = None):
        """Send message to Kafka topic"""
        try:
            producer = self.get_producer()
            future = producer.send(topic, value=message, key=key)
            result = future.get(timeout=10)
            logger.info(f"Message sent to topic {topic}: {result}")
            return True
        except KafkaError as e:
            logger.error(f"Failed to send message to topic {topic}: {e}")
            return False
    
    def consume_messages(self, topics: list, group_id: str, message_handler: Callable):
        """Consume messages from Kafka topics"""
        consumer = self.get_consumer(topics, group_id)
        logger.info(f"Started consuming from topics {topics} with group {group_id}")
        
        try:
            for message in consumer:
                try:
                    logger.info(f"Received message from topic {message.topic}: {message.value}")
                    message_handler(message.topic, message.value)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except KeyboardInterrupt:
            logger.info("Consumer interrupted")
        finally:
            consumer.close()
    
    def close(self):
        """Close producer and consumer connections"""
        if self.producer:
            self.producer.close()
        if self.consumer:
            self.consumer.close()

# Global instance
kafka_client = KafkaClient()

# Kafka topics
class Topics:
    STOCK_UPDATE = 'stock-update'
    ORDER_CREATED = 'order-created'
    ORDER_PROCESSED = 'order-processed'
    HEALTH_CHECK = 'health-check'
    SYSTEM_ERROR = 'system-error'
