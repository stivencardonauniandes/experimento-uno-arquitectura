import sys
import threading
from datetime import datetime

# Add parent directories to path
sys.path.append('/app')
sys.path.append('/app/shared')

from shared.kafka_client import kafka_client, Topics
from shared.database import db
from shared.models import Product, StockMovement, OrderStatus
from shared.utils import setup_logging

logger = setup_logging('inventory-kafka-consumer')

def handle_order_message(topic: str, message: dict):
    """Handle order-related messages"""
    try:
        if topic == Topics.ORDER_CREATED:
            handle_order_created(message)
        elif topic == Topics.ORDER_PROCESSED:
            handle_order_processed(message)
        else:
            logger.warning(f"Unknown topic: {topic}")
    except Exception as e:
        logger.error(f"Error handling message from topic {topic}: {e}")

def handle_order_created(message: dict):
    """Handle order created event - reserve stock"""
    try:
        order_id = message.get('order_id')
        order_type = message.get('order_type')
        order_items = message.get('order_items', [])
        
        logger.info(f"Processing order created: {order_id} (type: {order_type})")
        
        # For buy orders, we need to reserve stock
        if order_type == 'sell':
            success = True
            error_messages = []
            
            for item in order_items:
                product_id = item['product_id']
                quantity = item['quantity']
                
                product = Product.query.get(product_id)
                if not product:
                    error_messages.append(f"Product {product_id} not found")
                    success = False
                    continue
                
                if product.stock_quantity < quantity:
                    error_messages.append(f"Insufficient stock for product {product_id}: available {product.stock_quantity}, requested {quantity}")
                    success = False
                    continue
                
                # Reserve stock by reducing quantity
                product.stock_quantity -= quantity
                
                # Create stock movement record
                stock_movement = StockMovement(
                    product_id=product_id,
                    quantity_change=-quantity,
                    movement_type='sale_reservation',
                    reference_id=str(order_id),
                    notes=f"Stock reserved for order {order_id}"
                )
                
                db.session.add(stock_movement)
            
            if success:
                db.session.commit()
                logger.info(f"Stock reserved successfully for order {order_id}")
                
                # Send confirmation message
                response_message = {
                    'order_id': order_id,
                    'status': 'stock_reserved',
                    'timestamp': datetime.utcnow().isoformat()
                }
                kafka_client.send_message(Topics.ORDER_PROCESSED, response_message)
            else:
                db.session.rollback()
                logger.error(f"Failed to reserve stock for order {order_id}: {', '.join(error_messages)}")
                
                # Send failure message
                response_message = {
                    'order_id': order_id,
                    'status': 'stock_reservation_failed',
                    'errors': error_messages,
                    'timestamp': datetime.utcnow().isoformat()
                }
                kafka_client.send_message(Topics.ORDER_PROCESSED, response_message)
        
        elif order_type == 'buy':
            # For buy orders, we add stock after processing
            for item in order_items:
                product_id = item['product_id']
                quantity = item['quantity']
                
                product = Product.query.get(product_id)
                if product:
                    product.stock_quantity += quantity
                    
                    # Create stock movement record
                    stock_movement = StockMovement(
                        product_id=product_id,
                        quantity_change=quantity,
                        movement_type='purchase',
                        reference_id=str(order_id),
                        notes=f"Stock added from purchase order {order_id}"
                    )
                    
                    db.session.add(stock_movement)
            
            db.session.commit()
            logger.info(f"Stock added successfully for buy order {order_id}")
            
            # Send confirmation message
            response_message = {
                'order_id': order_id,
                'status': 'stock_updated',
                'timestamp': datetime.utcnow().isoformat()
            }
            kafka_client.send_message(Topics.ORDER_PROCESSED, response_message)
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing order created message: {e}")

def handle_order_processed(message: dict):
    """Handle order processed event"""
    try:
        order_id = message.get('order_id')
        status = message.get('status')
        
        logger.info(f"Order {order_id} processed with status: {status}")
        
        # If order was cancelled or failed, we might need to restore reserved stock
        if status in ['cancelled', 'failed']:
            # This would require more complex logic to track reservations
            # For now, just log the event
            logger.info(f"Order {order_id} was {status}, stock restoration might be needed")
            
    except Exception as e:
        logger.error(f"Error processing order processed message: {e}")

def start_kafka_consumer():
    """Start Kafka consumer for inventory service"""
    try:
        logger.info("Starting Kafka consumer for inventory service")
        
        topics = [Topics.ORDER_CREATED, Topics.ORDER_PROCESSED]
        group_id = 'inventory-service-group'
        
        kafka_client.consume_messages(topics, group_id, handle_order_message)
        
    except Exception as e:
        logger.error(f"Error in Kafka consumer: {e}")

if __name__ == "__main__":
    start_kafka_consumer()
