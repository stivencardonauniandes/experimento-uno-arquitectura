from flask import Flask, request, jsonify
from flask_migrate import upgrade
from datetime import datetime
from sqlalchemy import text
import os
import sys
import threading

# Add parent directories to path to import shared modules
sys.path.append('/app')
sys.path.append('/app/shared')

from shared.database import db, init_db, get_db_uri
from shared.models import Order, OrderItem, OrderStatus, OrderType
from shared.kafka_client import kafka_client, Topics
from shared.utils import setup_logging, validate_json, health_check_response, generate_order_number
from services.orders.kafka_consumer import start_kafka_consumer

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = get_db_uri('orders')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_db(app)

# Setup logging
logger = setup_logging('orders-service')

# API Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connectivity
        db.session.execute(text('SELECT 1'))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error(f"Database health check failed: {e}")
    
    status = "healthy" if db_status == "healthy" else "unhealthy"
    
    return jsonify(health_check_response(
        'orders-service', 
        status,
        {'database': db_status}
    )), 200 if status == "healthy" else 503

@app.route('/orders', methods=['GET'])
def get_orders():
    """Get all orders with optional filtering"""
    try:
        # Get query parameters
        status_filter = request.args.get('status')
        order_type_filter = request.args.get('type')
        limit = request.args.get('limit', type=int, default=50)
        offset = request.args.get('offset', type=int, default=0)
        
        query = Order.query
        
        # Apply filters
        if status_filter:
            try:
                status_enum = OrderStatus(status_filter.lower())
                query = query.filter(Order.status == status_enum)
            except ValueError:
                return jsonify({'error': f'Invalid status: {status_filter}'}), 400
        
        if order_type_filter:
            try:
                type_enum = OrderType(order_type_filter.lower())
                query = query.filter(Order.order_type == type_enum)
            except ValueError:
                return jsonify({'error': f'Invalid order type: {order_type_filter}'}), 400
        
        # Apply pagination and ordering
        orders = query.order_by(Order.created_at.desc()).offset(offset).limit(limit).all()
        
        # Include order items in response
        orders_data = []
        for order in orders:
            order_data = order.to_dict()
            order_data['items'] = [item.to_dict() for item in order.order_items]
            orders_data.append(order_data)
        
        return jsonify({
            'orders': orders_data,
            'total': query.count(),
            'limit': limit,
            'offset': offset
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get specific order"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        order_data = order.to_dict()
        order_data['items'] = [item.to_dict() for item in order.order_items]
        
        return jsonify(order_data), 200
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/orders', methods=['POST'])
@validate_json('order_type', 'customer_name', 'items')
def create_order():
    """Create new order"""
    try:
        data = request.get_json()
        
        # Validate order type
        try:
            order_type = OrderType(data['order_type'].lower())
        except ValueError:
            return jsonify({'error': f'Invalid order type: {data["order_type"]}'}), 400
        
        # Validate items
        items_data = data['items']
        if not items_data or not isinstance(items_data, list):
            return jsonify({'error': 'Items must be a non-empty list'}), 400
        
        # Calculate total amount
        total_amount = 0
        for item in items_data:
            if not all(key in item for key in ['product_id', 'product_name', 'quantity', 'unit_price']):
                return jsonify({'error': 'Each item must have product_id, product_name, quantity, and unit_price'}), 400
            
            if item['quantity'] <= 0 or item['unit_price'] <= 0:
                return jsonify({'error': 'Quantity and unit_price must be positive'}), 400
            
            item_total = item['quantity'] * item['unit_price']
            total_amount += item_total
            item['total_price'] = item_total
        
        # Create order
        order = Order(
            order_number=generate_order_number(),
            order_type=order_type,
            customer_name=data['customer_name'],
            customer_email=data.get('customer_email'),
            total_amount=total_amount
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        order_items = []
        for item_data in items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product_id'],
                product_name=item_data['product_name'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price']
            )
            db.session.add(order_item)
            order_items.append(order_item)
        
        db.session.commit()
        
        # Send order created message to Kafka
        order_message = {
            'order_id': order.id,
            'order_number': order.order_number,
            'order_type': order.order_type.value,
            'customer_name': order.customer_name,
            'customer_email': order.customer_email,
            'total_amount': float(order.total_amount),
            'order_items': [
                {
                    'product_id': item.product_id,
                    'product_name': item.product_name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.total_price)
                }
                for item in order_items
            ],
            'created_at': order.created_at.isoformat()
        }
        
        kafka_client.send_message(Topics.ORDER_CREATED, order_message)
        
        logger.info(f"Created order: {order.order_number}")
        
        # Prepare response
        order_data = order.to_dict()
        order_data['items'] = [item.to_dict() for item in order_items]
        
        return jsonify(order_data), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating order: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/orders/<int:order_id>/status', methods=['PUT'])
@validate_json('status')
def update_order_status(order_id):
    """Update order status"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        data = request.get_json()
        
        # Validate status
        try:
            new_status = OrderStatus(data['status'].lower())
        except ValueError:
            return jsonify({'error': f'Invalid status: {data["status"]}'}), 400
        
        # Update status
        old_status = order.status
        order.status = new_status
        
        # Set processed_at timestamp if order is completed
        if new_status == OrderStatus.COMPLETED:
            order.processed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send status update message to Kafka
        status_message = {
            'order_id': order.id,
            'order_number': order.order_number,
            'old_status': old_status.value,
            'new_status': new_status.value,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        kafka_client.send_message(Topics.ORDER_PROCESSED, status_message)
        
        logger.info(f"Updated order {order.order_number} status: {old_status.value} -> {new_status.value}")
        
        return jsonify(order.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating order {order_id} status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/orders/<int:order_id>', methods=['DELETE'])
def cancel_order(order_id):
    """Cancel order (soft delete by setting status to cancelled)"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Can only cancel pending or processing orders
        if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            return jsonify({'error': f'Cannot cancel order with status: {order.status.value}'}), 400
        
        old_status = order.status
        order.status = OrderStatus.CANCELLED
        
        db.session.commit()
        
        # Send cancellation message to Kafka
        cancellation_message = {
            'order_id': order.id,
            'order_number': order.order_number,
            'old_status': old_status.value,
            'new_status': OrderStatus.CANCELLED.value,
            'cancelled_at': datetime.utcnow().isoformat()
        }
        
        kafka_client.send_message(Topics.ORDER_PROCESSED, cancellation_message)
        
        logger.info(f"Cancelled order: {order.order_number}")
        
        return jsonify({'message': f'Order {order.order_number} cancelled successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cancelling order {order_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/orders/stats', methods=['GET'])
def get_order_stats():
    """Get order statistics"""
    try:
        stats = {}
        
        # Count orders by status
        for status in OrderStatus:
            count = Order.query.filter(Order.status == status).count()
            stats[f'orders_{status.value}'] = count
        
        # Count orders by type
        for order_type in OrderType:
            count = Order.query.filter(Order.order_type == order_type).count()
            stats[f'orders_{order_type.value}'] = count
        
        # Total orders
        stats['total_orders'] = Order.query.count()
        
        # Total revenue (completed orders only)
        completed_orders = Order.query.filter(Order.status == OrderStatus.COMPLETED).all()
        stats['total_revenue'] = sum(float(order.total_amount) for order in completed_orders)
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting order stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def create_tables():
    """Create database tables"""
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")

if __name__ == '__main__':
    # Create tables
    create_tables()
    
    # Start Kafka consumer in background thread
    consumer_thread = threading.Thread(target=start_kafka_consumer, daemon=True)
    consumer_thread.start()
    logger.info("Started Kafka consumer thread")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5002, debug=False)
