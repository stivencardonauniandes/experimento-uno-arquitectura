import sys
from datetime import datetime
from typing import Callable

# Add parent directories to path
sys.path.append('/app')
sys.path.append('/app/shared')

from shared.kafka_client import kafka_client, Topics
from shared.utils import setup_logging

logger = setup_logging('kafka-monitor')

def handle_monitoring_message(topic: str, message: dict, stats_callback: Callable, alert_callback: Callable):
    """Handle messages for monitoring purposes"""
    try:
        # Update message statistics
        stats_callback(topic)
        
        logger.info(f"Monitored message from topic {topic}: {message}")
        
        # Analyze message for potential issues
        if topic == Topics.ORDER_CREATED:
            # Monitor order creation
            order_type = message.get('order_type')
            total_amount = message.get('total_amount', 0)
            
            # Alert for high-value orders
            if total_amount > 10000:
                alert_callback(
                    'high_value_order',
                    f"High value {order_type} order created: ${total_amount}",
                    'orders-service',
                    'info'
                )
        
        elif topic == Topics.ORDER_PROCESSED:
            # Monitor order processing
            status = message.get('status')
            order_id = message.get('order_id')
            
            if status in ['failed', 'cancelled']:
                alert_callback(
                    'order_processing_issue',
                    f"Order {order_id} processing issue: {status}",
                    'orders-service',
                    'warning'
                )
            elif status == 'stock_reservation_failed':
                errors = message.get('errors', [])
                alert_callback(
                    'stock_reservation_failed',
                    f"Stock reservation failed for order {order_id}: {', '.join(errors)}",
                    'inventory-service',
                    'warning'
                )
        
        elif topic == Topics.STOCK_UPDATE:
            # Monitor stock updates
            product_id = message.get('product_id')
            new_quantity = message.get('new_quantity', 0)
            movement_type = message.get('movement_type')
            
            # Alert for low stock
            if new_quantity <= 5:
                alert_callback(
                    'low_stock',
                    f"Low stock alert for product {product_id}: {new_quantity} units remaining",
                    'inventory-service',
                    'warning'
                )
            
            # Alert for negative stock (shouldn't happen but good to monitor)
            if new_quantity < 0:
                alert_callback(
                    'negative_stock',
                    f"Negative stock detected for product {product_id}: {new_quantity}",
                    'inventory-service',
                    'critical'
                )
        
        elif topic == Topics.HEALTH_CHECK:
            # Monitor health check messages
            service = message.get('service')
            status = message.get('status')
            
            if status != 'healthy':
                alert_callback(
                    'service_health_issue',
                    f"Service {service} reported unhealthy status: {status}",
                    service,
                    'warning'
                )
        
    except Exception as e:
        logger.error(f"Error handling monitoring message from topic {topic}: {e}")
        alert_callback(
            'monitoring_error',
            f"Error processing message from {topic}: {str(e)}",
            'monitor-service',
            'error'
        )

def send_health_check_message():
    """Send periodic health check message to Kafka"""
    try:
        health_message = {
            'service': 'monitor-service',
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Monitor service health check'
        }
        
        kafka_client.send_message(Topics.HEALTH_CHECK, health_message)
        logger.debug("Sent health check message to Kafka")
        
    except Exception as e:
        logger.error(f"Error sending health check message: {e}")

def start_kafka_monitor(stats_callback: Callable, alert_callback: Callable):
    """Start Kafka monitoring"""
    try:
        logger.info("Starting Kafka monitor")
        
        # Send initial health check
        send_health_check_message()
        
        # Monitor all topics
        topics = [
            Topics.ORDER_CREATED,
            Topics.ORDER_PROCESSED,
            Topics.STOCK_UPDATE,
            Topics.HEALTH_CHECK
        ]
        
        group_id = 'monitor-service-group'
        
        def message_handler(topic: str, message: dict):
            handle_monitoring_message(topic, message, stats_callback, alert_callback)
        
        kafka_client.consume_messages(topics, group_id, message_handler)
        
    except Exception as e:
        logger.error(f"Error in Kafka monitor: {e}")
        alert_callback(
            'kafka_monitor_error',
            f"Kafka monitor error: {str(e)}",
            'monitor-service',
            'critical'
        )

if __name__ == "__main__":
    # Test function for development
    def test_stats_callback(topic):
        print(f"Stats: Message from {topic}")
    
    def test_alert_callback(alert_type, message, service, severity):
        print(f"Alert [{severity}]: {alert_type} - {message} (service: {service})")
    
    start_kafka_monitor(test_stats_callback, test_alert_callback)
