from datetime import datetime
from enum import Enum
from shared.database import db

class OrderStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class OrderType(Enum):
    BUY = "buy"
    SELL = "sell"

# Inventory Service Models
class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    min_stock_level = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': float(self.price),
            'stock_quantity': self.stock_quantity,
            'min_stock_level': self.min_stock_level,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity_change = db.Column(db.Integer, nullable=False)  # Positive for incoming, negative for outgoing
    movement_type = db.Column(db.String(50), nullable=False)  # 'purchase', 'sale', 'adjustment'
    reference_id = db.Column(db.String(100))  # Order ID or other reference
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', backref=db.backref('stock_movements', lazy=True))
    
    def __repr__(self):
        return f'<StockMovement {self.product_id}: {self.quantity_change}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'quantity_change': self.quantity_change,
            'movement_type': self.movement_type,
            'reference_id': self.reference_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }

# Orders Service Models  
class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    order_type = db.Column(db.Enum(OrderType), nullable=False)
    status = db.Column(db.Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100))
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Order {self.order_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'order_type': self.order_type.value,
            'status': self.status.value,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'total_amount': float(self.total_amount),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)  # Reference to product in inventory service
    product_name = db.Column(db.String(100), nullable=False)  # Denormalized for performance
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    order = db.relationship('Order', backref=db.backref('order_items', lazy=True, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<OrderItem {self.product_name}: {self.quantity}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_price': float(self.total_price)
        }
