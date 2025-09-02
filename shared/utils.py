import uuid
import logging
from datetime import datetime
from functools import wraps
from flask import request, jsonify

def generate_order_number():
    """Generate unique order number"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"ORD-{timestamp}-{unique_id}"

def setup_logging(service_name: str):
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format=f'%(asctime)s - {service_name} - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'/app/logs/{service_name}.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(service_name)

def validate_json(*required_fields):
    """Decorator to validate JSON request data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body is required'}), 400
            
            missing_fields = []
            for field in required_fields:
                if field not in data or data[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                return jsonify({
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def health_check_response(service_name: str, status: str = "healthy", additional_info: dict = None):
    """Generate standardized health check response"""
    response = {
        'service': service_name,
        'status': status,
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }
    
    if additional_info:
        response.update(additional_info)
    
    return response
