import sys
import threading
from datetime import datetime

# Add parent directories to path
sys.path.append('/app')
sys.path.append('/app/shared')

from shared.kafka_client import kafka_client, Topics
from shared.database import db
from shared.models import Order, OrderStatus
from shared.utils import setup_logging

logger = setup_logging('orders-kafka-consumer')

def handle_inventory_message(topic: str, message: dict):
    """Handle inventory-related messages"""
    try:
        if topic == Topics.STOCK_UPDATE:
            handle_stock_update(message)
        elif topic == Topics.ORDER_PROCESSED:
            handle_order_processed_response(message)
        else:
            logger.warning(f"Unknown topic: {topic}")
    except Exception as e:
        logger.error(f"Error handling message from topic {topic}: {e}")

def handle_stock_update(message: dict):
    """Handle stock update notifications from inventory service"""
    try:
        product_id = message.get('product_id')
        old_quantity = message.get('old_quantity')
        new_quantity = message.get('new_quantity')
        quantity_change = message.get('quantity_change')
        movement_type = message.get('movement_type')
        reference_id = message.get('reference_id')
        
        logger.info(f"Stock update received for product {product_id}: {old_quantity} -> {new_quantity} (change: {quantity_change}, type: {movement_type})")
        
        # If this stock update is related to an order (has reference_id)
        if reference_id and reference_id.isdigit():
            order_id = int(reference_id)
            order = Order.query.get(order_id)
            
            if order:
                logger.info(f"Stock update for order {order.order_number} processed")
                
                # You could add additional logic here to update order status
                # based on stock movements
                
    except Exception as e:
        logger.error(f"Error processing stock update message: {e}")

def handle_order_processed_response(message: dict):
    """Handle responses from inventory service about order processing"""
    try:
        order_id = message.get('order_id')
        status = message.get('status')
        errors = message.get('errors', [])
    
        if not order_id:
            logger.error("Received order processed message without order_id")
            return
        
        order = Order.query.get(order_id)
        if not order:
            logger.error(f"Order {order_id} not found")
            return
            
        logger.info(f"Received inventory response for order {order.order_number}: {status}")
            
            # Update order status based on inventory service response
        if status == 'stock_reserved':
            # Stock successfully reserved for sell order
            if order.status == OrderStatus.PENDING:
                order.status = OrderStatus.PROCESSING
                db.session.commit()
                logger.info(f"Order {order.order_number} moved to PROCESSING status")
                    
            elif status == 'stock_updated':
                # Stock updated for buy order
                if order.status == OrderStatus.PENDING:
                    order.status = OrderStatus.PROCESSING
                    db.session.commit()
                    logger.info(f"Buy order {order.order_number} moved to PROCESSING status")
                    
            elif status == 'stock_reservation_failed':
                # Stock reservation failed
                order.status = OrderStatus.FAILED
                db.session.commit()
                logger.error(f"Order {order.order_number} failed due to stock issues: {', '.join(errors)}")
                
            else:
                logger.warning(f"Unknown order processing status: {status}")
                
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing order processed response: {e}")

def start_kafka_consumer():
    """Start Kafka consumer for orders service"""
    try:
        logger.info("Starting Kafka consumer for orders service")
        
        topics = [Topics.STOCK_UPDATE, Topics.ORDER_PROCESSED]
        group_id = 'orders-service-group'
        
        kafka_client.consume_messages(topics, group_id, handle_inventory_message)
        
    except Exception as e:
        logger.error(f"Error in Kafka consumer: {e}")

def start_kafka_consumer_with_app(app):
    """Start Kafka consumer with Flask app context"""
    def consumer_with_context():
        try:
            logger.info("Starting Kafka consumer for orders service with app context")
            
            topics = [Topics.STOCK_UPDATE, Topics.ORDER_PROCESSED]
            group_id = 'orders-service-group'
            
            def message_handler_with_context(topic: str, message: dict):
                with app.app_context():
                    handle_inventory_message(topic, message)
            
            kafka_client.consume_messages(topics, group_id, message_handler_with_context)
            
        except Exception as e:
            logger.error(f"Error in Kafka consumer: {e}")
    
    return consumer_with_context

if __name__ == "__main__":
    start_kafka_consumer()
