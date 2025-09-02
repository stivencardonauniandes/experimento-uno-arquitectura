from flask import Flask, jsonify
from datetime import datetime, timedelta
import requests
import threading
import time
import os
import sys
from collections import defaultdict, deque

# Add parent directories to path
sys.path.append('/app')
sys.path.append('/app/shared')

from shared.kafka_client import kafka_client, Topics
from shared.utils import setup_logging, health_check_response
from services.monitor.health_checker import HealthChecker
from services.monitor.kafka_monitor import start_kafka_monitor

app = Flask(__name__)

# Setup logging
logger = setup_logging('monitor-service')

# Global variables for monitoring data
health_checker = HealthChecker()
service_health_history = defaultdict(lambda: deque(maxlen=100))  # Keep last 100 health checks
kafka_message_stats = defaultdict(int)
system_alerts = deque(maxlen=50)  # Keep last 50 alerts

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitor service itself"""
    return jsonify(health_check_response('monitor-service')), 200

@app.route('/services/health', methods=['GET'])
def get_services_health():
    """Get current health status of all monitored services"""
    try:
        services_status = health_checker.get_all_services_status()
        
        # Add timestamp
        response = {
            'timestamp': datetime.utcnow().isoformat(),
            'services': services_status,
            'overall_status': 'healthy' if all(
                service['status'] == 'healthy' 
                for service in services_status.values()
            ) else 'degraded'
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting services health: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/services/<service_name>/health', methods=['GET'])
def get_service_health(service_name):
    """Get health status of specific service"""
    try:
        service_status = health_checker.get_service_status(service_name)
        
        if not service_status:
            return jsonify({'error': f'Service {service_name} not found'}), 404
        
        return jsonify(service_status), 200
        
    except Exception as e:
        logger.error(f"Error getting health for service {service_name}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/services/<service_name>/history', methods=['GET'])
def get_service_health_history(service_name):
    """Get health history for specific service"""
    try:
        if service_name not in service_health_history:
            return jsonify({'error': f'No history found for service {service_name}'}), 404
        
        history = list(service_health_history[service_name])
        
        # Calculate uptime percentage
        total_checks = len(history)
        healthy_checks = sum(1 for check in history if check.get('status') == 'healthy')
        uptime_percentage = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        
        response = {
            'service': service_name,
            'total_checks': total_checks,
            'healthy_checks': healthy_checks,
            'uptime_percentage': round(uptime_percentage, 2),
            'history': history
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting history for service {service_name}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/kafka/stats', methods=['GET'])
def get_kafka_stats():
    """Get Kafka message statistics"""
    try:
        response = {
            'timestamp': datetime.utcnow().isoformat(),
            'message_stats': dict(kafka_message_stats),
            'total_messages': sum(kafka_message_stats.values())
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting Kafka stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Get system alerts"""
    try:
        response = {
            'timestamp': datetime.utcnow().isoformat(),
            'alerts': list(system_alerts),
            'total_alerts': len(system_alerts)
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/dashboard', methods=['GET'])
def get_dashboard():
    """Get comprehensive dashboard data"""
    try:
        services_status = health_checker.get_all_services_status()
        
        # Calculate overall system health
        healthy_services = sum(1 for service in services_status.values() if service['status'] == 'healthy')
        total_services = len(services_status)
        system_health_percentage = (healthy_services / total_services * 100) if total_services > 0 else 0
        
        # Get recent alerts (last 10)
        recent_alerts = list(system_alerts)[-10:]
        
        response = {
            'timestamp': datetime.utcnow().isoformat(),
            'system_health': {
                'overall_status': 'healthy' if system_health_percentage >= 100 else 'degraded',
                'health_percentage': round(system_health_percentage, 2),
                'healthy_services': healthy_services,
                'total_services': total_services
            },
            'services': services_status,
            'kafka_stats': {
                'message_stats': dict(kafka_message_stats),
                'total_messages': sum(kafka_message_stats.values())
            },
            'recent_alerts': recent_alerts,
            'total_alerts': len(system_alerts)
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def add_alert(alert_type: str, message: str, service: str = None, severity: str = 'warning'):
    """Add system alert"""
    alert = {
        'timestamp': datetime.utcnow().isoformat(),
        'type': alert_type,
        'message': message,
        'service': service,
        'severity': severity
    }
    
    system_alerts.append(alert)
    logger.warning(f"Alert added: {alert}")

def update_service_health_history(service_name: str, health_data: dict):
    """Update health history for a service"""
    health_record = {
        'timestamp': datetime.utcnow().isoformat(),
        'status': health_data.get('status', 'unknown'),
        'response_time': health_data.get('response_time'),
        'details': health_data.get('details', {})
    }
    
    service_health_history[service_name].append(health_record)

def update_kafka_message_stats(topic: str):
    """Update Kafka message statistics"""
    kafka_message_stats[topic] += 1

def start_health_monitoring():
    """Start periodic health monitoring"""
    def monitor_loop():
        while True:
            try:
                logger.info("Running health checks...")
                
                # Check all services
                services_status = health_checker.get_all_services_status()
                
                for service_name, status in services_status.items():
                    # Update history
                    update_service_health_history(service_name, status)
                    
                    # Generate alerts for unhealthy services
                    if status['status'] != 'healthy':
                        add_alert(
                            'service_unhealthy',
                            f"Service {service_name} is {status['status']}",
                            service_name,
                            'critical' if status['status'] == 'down' else 'warning'
                        )
                
                # Sleep for 30 seconds before next check
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(30)
    
    # Start monitoring in background thread
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    logger.info("Started health monitoring thread")

if __name__ == '__main__':
    # Start health monitoring
    start_health_monitoring()
    
    # Start Kafka monitoring
    kafka_monitor_thread = threading.Thread(
        target=start_kafka_monitor, 
        args=(update_kafka_message_stats, add_alert),
        daemon=True
    )
    kafka_monitor_thread.start()
    logger.info("Started Kafka monitoring thread")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5003, debug=False)
