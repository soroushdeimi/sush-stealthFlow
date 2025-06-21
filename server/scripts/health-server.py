#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
StealthFlow Health Check Server
Health monitoring and metrics server for StealthFlow
"""

import json
import time
import socket
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import os
import sys

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Handler for health check and metrics requests"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_health_response()
        elif self.path == '/metrics':
            self.send_metrics_response()
        elif self.path == '/status':
            self.send_status_response()
        else:
            self.send_not_found()
    
    def send_health_response(self):
        """Send health check response"""
        try:
            # Check service status
            xray_status = self.check_xray_status()
            nginx_status = self.check_nginx_status()
            
            # Generate health response
            health_data = {
                'status': 'healthy' if (xray_status and nginx_status) else 'unhealthy',
                'service': 'stealthflow-server',
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+00:00'),
                'version': '1.0.0',
                'components': {
                    'xray': {
                        'status': 'up' if xray_status else 'down',
                        'port': 444,
                        'description': 'Xray proxy server'
                    },
                    'nginx': {
                        'status': 'up' if nginx_status else 'down',
                        'port': 80,
                        'description': 'Nginx web server'
                    }
                },
                'uptime': self.get_uptime(),
                'memory_usage': self.get_memory_usage(),
                'disk_usage': self.get_disk_usage()
            }
            
            # Send response
            status_code = 200 if health_data['status'] == 'healthy' else 503
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            response = json.dumps(health_data, indent=2)
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error_response(str(e))
    
    def send_metrics_response(self):
        """Send Prometheus metrics"""
        try:
            metrics = []
            
            # Service availability metrics
            metrics.append('# HELP stealthflow_up Service availability (1 = up, 0 = down)')
            metrics.append('# TYPE stealthflow_up gauge')
            metrics.append(f'stealthflow_up{{service="xray"}} {1 if self.check_xray_status() else 0}')
            metrics.append(f'stealthflow_up{{service="nginx"}} {1 if self.check_nginx_status() else 0}')
            
            # Uptime metric
            metrics.append('# HELP stealthflow_uptime_seconds Service uptime in seconds')
            metrics.append('# TYPE stealthflow_uptime_seconds counter')
            metrics.append(f'stealthflow_uptime_seconds {self.get_uptime()}')
            
            # Memory usage metric
            memory_usage = self.get_memory_usage()
            if memory_usage > 0:
                metrics.append('# HELP stealthflow_memory_usage_bytes Memory usage in bytes')
                metrics.append('# TYPE stealthflow_memory_usage_bytes gauge')
                metrics.append(f'stealthflow_memory_usage_bytes {memory_usage}')
            
            # Connection metrics
            metrics.append('# HELP stealthflow_connections_total Total connections handled')
            metrics.append('# TYPE stealthflow_connections_total counter')
            metrics.append('stealthflow_connections_total 0')  # Placeholder
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            response = '\n'.join(metrics) + '\n'
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error_response(str(e))
    
    def send_status_response(self):
        """Send detailed status information"""
        try:
            status_data = {
                'server': {
                    'name': 'stealthflow-health-server',
                    'version': '1.0.0',
                    'uptime': self.get_uptime(),
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+00:00')
                },
                'services': {
                    'xray': {
                        'running': self.check_xray_status(),
                        'port': 444,
                        'protocol': 'VLESS/REALITY'
                    },
                    'nginx': {
                        'running': self.check_nginx_status(),
                        'port': 80,
                        'protocol': 'HTTP/HTTPS'
                    }
                },
                'system': {
                    'memory_usage': self.get_memory_usage(),
                    'disk_usage': self.get_disk_usage(),
                    'load_average': self.get_load_average()
                }
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = json.dumps(status_data, indent=2)
            self.wfile.write(response.encode('utf-8'))
            
        except Exception as e:
            self.send_error_response(str(e))
    
    def check_xray_status(self):
        """Check Xray service status"""
        try:
            # Check if Xray port is listening
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 444))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def check_nginx_status(self):
        """Check Nginx service status"""
        try:
            # Check if Nginx port is listening
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 80))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def get_uptime(self):
        """Get system uptime in seconds"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                return int(uptime_seconds)
        except Exception:
            return 0
    
    def get_memory_usage(self):
        """Get memory usage in bytes"""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                
            mem_total = 0
            mem_available = 0
            
            for line in lines:
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1]) * 1024  # Convert KB to bytes
                elif line.startswith('MemAvailable:'):
                    mem_available = int(line.split()[1]) * 1024  # Convert KB to bytes
            
            return mem_total - mem_available if mem_total and mem_available else 0
        except Exception:
            return 0
    
    def get_disk_usage(self):
        """Get disk usage percentage"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            return {
                'total': total,
                'used': used,
                'free': free,
                'percentage': round((used / total) * 100, 2)
            }
        except Exception:
            return {'total': 0, 'used': 0, 'free': 0, 'percentage': 0}
    
    def get_load_average(self):
        """Get system load average"""
        try:
            with open('/proc/loadavg', 'r') as f:
                load_avg = f.readline().split()
                return {
                    '1min': float(load_avg[0]),
                    '5min': float(load_avg[1]),
                    '15min': float(load_avg[2])
                }
        except Exception:
            return {'1min': 0.0, '5min': 0.0, '15min': 0.0}
    
    def send_error_response(self, error_message):
        """Send error response"""
        self.send_response(500)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        error_data = {
            'status': 'error',
            'message': error_message,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S+00:00')
        }
        
        response = json.dumps(error_data)
        self.wfile.write(response.encode('utf-8'))
    
    def send_not_found(self):
        """Send 404 response"""
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        error_data = {
            'status': 'not_found',
            'message': 'Endpoint not found',
            'available_endpoints': ['/health', '/metrics', '/status'],
            'description': 'StealthFlow Health Check Server'
        }
        
        response = json.dumps(error_data)
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Disable HTTP server access logs"""
        pass

def run_health_server():
    """Run the health check server"""
    port = int(os.getenv('HEALTH_PORT', 9000))
    host = os.getenv('HEALTH_HOST', '0.0.0.0')
    
    try:
        server = HTTPServer((host, port), HealthCheckHandler)
        print(f"StealthFlow Health Check Server starting on {host}:{port}")
        print(f"Available endpoints:")
        print(f"  - http://{host}:{port}/health")
        print(f"  - http://{host}:{port}/metrics")
        print(f"  - http://{host}:{port}/status")
        print(f"Press Ctrl+C to stop the server")
        
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nHealth check server stopped gracefully")
        server.shutdown()
    except Exception as e:
        print(f"Health check server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_health_server()
