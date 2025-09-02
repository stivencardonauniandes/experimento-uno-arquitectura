import requests
import time
import os
from datetime import datetime
from typing import Dict, Any
import sys

sys.path.append('/app')
sys.path.append('/app/shared')

from shared.utils import setup_logging

logger = setup_logging('health-checker')

class HealthChecker:
    def __init__(self):
        self.services = {
            'inventory-service': {
                'url': os.getenv('INVENTORY_SERVICE_URL', 'http://inventory-service:5001/health'),
                'timeout': 5
            },
            'orders-service': {
                'url': os.getenv('ORDERS_SERVICE_URL', 'http://orders-service:5002/health'),
                'timeout': 5
            }
        }
        
        # Add external services
        self.external_services = {
            'postgres': {
                'url': os.getenv('POSTGRES_URL', 'http://postgres:5432'),
                'timeout': 3,
                'check_method': 'tcp'  # Just check if port is open
            },
            'kafka': {
                'url': os.getenv('KAFKA_URL', 'http://kafka:9092'),
                'timeout': 3,
                'check_method': 'tcp'
            }
        }
    
    def check_service_health(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Check health of a specific service"""
        start_time = time.time()
        
        try:
            response = requests.get(
                service_config['url'],
                timeout=service_config['timeout']
            )
            
            response_time = round((time.time() - start_time) * 1000, 2)  # ms
            
            if response.status_code == 200:
                health_data = response.json()
                return {
                    'status': 'healthy',
                    'response_time': response_time,
                    'details': health_data,
                    'last_checked': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'response_time': response_time,
                    'details': {
                        'status_code': response.status_code,
                        'error': f'HTTP {response.status_code}'
                    },
                    'last_checked': datetime.utcnow().isoformat()
                }
                
        except requests.exceptions.Timeout:
            response_time = round((time.time() - start_time) * 1000, 2)
            return {
                'status': 'down',
                'response_time': response_time,
                'details': {'error': 'Request timeout'},
                'last_checked': datetime.utcnow().isoformat()
            }
            
        except requests.exceptions.ConnectionError:
            response_time = round((time.time() - start_time) * 1000, 2)
            return {
                'status': 'down',
                'response_time': response_time,
                'details': {'error': 'Connection failed'},
                'last_checked': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            response_time = round((time.time() - start_time) * 1000, 2)
            return {
                'status': 'down',
                'response_time': response_time,
                'details': {'error': str(e)},
                'last_checked': datetime.utcnow().isoformat()
            }
    
    def check_tcp_service(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Check TCP service availability"""
        import socket
        
        start_time = time.time()
        
        try:
            # Parse URL to get host and port
            url = service_config['url'].replace('http://', '').replace('https://', '')
            if ':' in url:
                host, port = url.split(':')
                port = int(port)
            else:
                host = url
                port = 80
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(service_config['timeout'])
            result = sock.connect_ex((host, port))
            sock.close()
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if result == 0:
                return {
                    'status': 'healthy',
                    'response_time': response_time,
                    'details': {'connection': 'successful'},
                    'last_checked': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': 'down',
                    'response_time': response_time,
                    'details': {'connection': 'failed', 'error_code': result},
                    'last_checked': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            response_time = round((time.time() - start_time) * 1000, 2)
            return {
                'status': 'down',
                'response_time': response_time,
                'details': {'error': str(e)},
                'last_checked': datetime.utcnow().isoformat()
            }
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get status of a specific service"""
        if service_name in self.services:
            return self.check_service_health(service_name, self.services[service_name])
        elif service_name in self.external_services:
            service_config = self.external_services[service_name]
            if service_config.get('check_method') == 'tcp':
                return self.check_tcp_service(service_name, service_config)
            else:
                return self.check_service_health(service_name, service_config)
        else:
            return None
    
    def get_all_services_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all monitored services"""
        all_status = {}
        
        # Check application services
        for service_name, service_config in self.services.items():
            try:
                status = self.check_service_health(service_name, service_config)
                all_status[service_name] = status
                logger.debug(f"Health check for {service_name}: {status['status']}")
            except Exception as e:
                logger.error(f"Error checking {service_name}: {e}")
                all_status[service_name] = {
                    'status': 'error',
                    'details': {'error': str(e)},
                    'last_checked': datetime.utcnow().isoformat()
                }
        
        # Check external services
        for service_name, service_config in self.external_services.items():
            try:
                if service_config.get('check_method') == 'tcp':
                    status = self.check_tcp_service(service_name, service_config)
                else:
                    status = self.check_service_health(service_name, service_config)
                
                all_status[service_name] = status
                logger.debug(f"Health check for {service_name}: {status['status']}")
            except Exception as e:
                logger.error(f"Error checking {service_name}: {e}")
                all_status[service_name] = {
                    'status': 'error',
                    'details': {'error': str(e)},
                    'last_checked': datetime.utcnow().isoformat()
                }
        
        return all_status
