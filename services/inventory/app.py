from flask import Flask, request, jsonify
from flask_migrate import upgrade
from sqlalchemy import text
import os
import sys
import threading

# Add parent directories to path to import shared modules
sys.path.append('/app')
sys.path.append('/app/shared')

from shared.database import db, init_db, get_db_uri
from shared.models import Product, StockMovement
from shared.kafka_client import kafka_client, Topics
from shared.utils import setup_logging, validate_json, health_check_response
from services.inventory.kafka_consumer import start_kafka_consumer_with_app

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = get_db_uri('inventory')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_db(app)

# Setup logging
logger = setup_logging('inventory-service')

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
        'inventory-service', 
        status,
        {'database': db_status}
    )), 200 if status == "healthy" else 503

@app.route('/products', methods=['GET'])
def get_products():
    """Get all products"""
    try:
        products = Product.query.all()
        return jsonify([product.to_dict() for product in products]), 200
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get specific product"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        return jsonify(product.to_dict()), 200
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/products', methods=['POST'])
@validate_json('name', 'price', 'stock_quantity')
def create_product():
    """Create new product"""
    try:
        data = request.get_json()
        
        product = Product(
            name=data['name'],
            description=data.get('description', ''),
            price=data['price'],
            stock_quantity=data['stock_quantity'],
            min_stock_level=data.get('min_stock_level', 10)
        )
        
        db.session.add(product)
        db.session.commit()
        
        logger.info(f"Created product: {product.name}")
        return jsonify(product.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating product: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update product"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Update fields if provided
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = data['price']
        if 'min_stock_level' in data:
            product.min_stock_level = data['min_stock_level']
        
        db.session.commit()
        
        logger.info(f"Updated product: {product.name}")
        return jsonify(product.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating product {product_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/products/<int:product_id>/stock', methods=['POST'])
@validate_json('quantity_change', 'movement_type')
def update_stock(product_id):
    """Update product stock"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        data = request.get_json()
        quantity_change = int(data['quantity_change'])
        
        # Check if there's enough stock for negative changes
        if quantity_change < 0 and product.stock_quantity + quantity_change < 0:
            return jsonify({'error': 'Insufficient stock'}), 400
        
        # Update stock
        old_quantity = product.stock_quantity
        product.stock_quantity += quantity_change
        
        # Create stock movement record
        stock_movement = StockMovement(
            product_id=product_id,
            quantity_change=quantity_change,
            movement_type=data['movement_type'],
            reference_id=data.get('reference_id'),
            notes=data.get('notes')
        )
        
        db.session.add(stock_movement)
        db.session.commit()
        
        # Send stock update notification via Kafka
        stock_update_message = {
            'product_id': product_id,
            'old_quantity': old_quantity,
            'new_quantity': product.stock_quantity,
            'quantity_change': quantity_change,
            'movement_type': data['movement_type'],
            'reference_id': data.get('reference_id')
        }
        
        kafka_client.send_message(Topics.STOCK_UPDATE, stock_update_message)
        
        logger.info(f"Updated stock for product {product_id}: {old_quantity} -> {product.stock_quantity}")
        
        return jsonify({
            'product': product.to_dict(),
            'stock_movement': stock_movement.to_dict()
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid quantity_change value'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating stock for product {product_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/products/<int:product_id>/movements', methods=['GET'])
def get_stock_movements(product_id):
    """Get stock movements for a product"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        movements = StockMovement.query.filter_by(product_id=product_id).order_by(StockMovement.created_at.desc()).all()
        return jsonify([movement.to_dict() for movement in movements]), 200
    except Exception as e:
        logger.error(f"Error getting stock movements for product {product_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/products/low-stock', methods=['GET'])
def get_low_stock_products():
    """Get products with low stock levels"""
    try:
        low_stock_products = Product.query.filter(Product.stock_quantity <= Product.min_stock_level).all()
        return jsonify([product.to_dict() for product in low_stock_products]), 200
    except Exception as e:
        logger.error(f"Error getting low stock products: {e}")
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
    
    # Start Kafka consumer in background thread with app context
    consumer_func = start_kafka_consumer_with_app(app)
    consumer_thread = threading.Thread(target=consumer_func, daemon=True)
    consumer_thread.start()
    logger.info("Started Kafka consumer thread")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5001, debug=False)
