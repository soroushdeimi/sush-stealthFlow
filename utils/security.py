#!/usr/bin/env python3
"""
StealthFlow Security Module
Comprehensive security utilities for input validation, sanitization, and security checks
"""

import re
import ipaddress
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
import logging
import hashlib
import secrets
import time
from datetime import datetime, timedelta

logger = logging.getLogger('StealthFlow.Security')


class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass


class InputValidator:
    """Comprehensive input validation utilities"""
    
    # Common patterns
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    DOMAIN_PATTERN = re.compile(r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$')
    BASE64_PATTERN = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')
    HEX_PATTERN = re.compile(r'^[0-9a-fA-F]+$')
    
    # Dangerous characters that should not appear in most inputs
    DANGEROUS_CHARS = ['<', '>', '"', "'", '`', '\n', '\r', '\0', '\x1a']
    
    @classmethod
    def validate_server_address(cls, address: str, allow_ip: bool = True, allow_domain: bool = True) -> bool:
        """Validate server address (IP or domain)"""
        if not isinstance(address, str):
            return False
        
        if not address or len(address) > 253:  # RFC 1035 limit
            return False
        
        # Check for dangerous characters
        if any(char in address for char in cls.DANGEROUS_CHARS):
            return False
        
        # Try as IP address
        if allow_ip:
            try:
                ipaddress.ip_address(address)
                return True
            except ValueError:
                pass
        
        # Try as domain name
        if allow_domain:
            return bool(cls.DOMAIN_PATTERN.match(address))
        
        return False
    
    @classmethod
    def validate_port(cls, port: Any) -> bool:
        """Validate port number"""
        try:
            port_int = int(port)
            return 1 <= port_int <= 65535
        except (ValueError, TypeError):
            return False
    
    @classmethod
    def validate_uuid(cls, uuid_str: str) -> bool:
        """Validate UUID format"""
        if not isinstance(uuid_str, str):
            return False
        return bool(cls.UUID_PATTERN.match(uuid_str))
    
    @classmethod
    def validate_base64(cls, data: str, min_length: int = 1, max_length: int = 1024) -> bool:
        """Validate base64 encoded data"""
        if not isinstance(data, str):
            return False
        
        if not (min_length <= len(data) <= max_length):
            return False
        
        return bool(cls.BASE64_PATTERN.match(data))
    
    @classmethod
    def validate_hex(cls, data: str, min_length: int = 1, max_length: int = 128) -> bool:
        """Validate hexadecimal string"""
        if not isinstance(data, str):
            return False
        
        if not (min_length <= len(data) <= max_length):
            return False
        
        return bool(cls.HEX_PATTERN.match(data))
    
    @classmethod
    def validate_url(cls, url: str, allowed_schemes: Optional[List[str]] = None) -> bool:
        """Validate URL format and security"""
        if not isinstance(url, str):
            return False
        
        # Length check
        if len(url) > 2048:  # RFC 7230 recommendation
            return False
        
        # Parse URL
        try:
            parsed = urllib.parse.urlparse(url)
        except Exception:
            return False
        
        # Check scheme
        if allowed_schemes is None:
            allowed_schemes = ['http', 'https', 'ws', 'wss']
        
        if parsed.scheme not in allowed_schemes:
            return False
        
        # Check for dangerous characters
        if any(char in url for char in cls.DANGEROUS_CHARS):
            return False
        
        # Validate hostname
        if parsed.hostname:
            return cls.validate_server_address(parsed.hostname)
        
        return True
    
    @classmethod
    def validate_password(cls, password: str, min_length: int = 8, max_length: int = 128) -> bool:
        """Validate password strength"""
        if not isinstance(password, str):
            return False
        
        if not (min_length <= len(password) <= max_length):
            return False
        
        # Check for dangerous characters that could indicate injection
        dangerous_sql_chars = [';', '--', '/*', '*/', 'xp_', 'sp_']
        if any(char in password.lower() for char in dangerous_sql_chars):
            return False
        
        return True
    
    @classmethod
    def sanitize_string(cls, data: str, max_length: int = 256, allow_unicode: bool = False) -> str:
        """Sanitize string input"""
        if not isinstance(data, str):
            raise SecurityError("Input must be string")
        
        # Remove null bytes and control characters
        data = ''.join(char for char in data if ord(char) >= 32 or char in ['\n', '\r', '\t'])
        
        # Remove dangerous characters
        for char in cls.DANGEROUS_CHARS:
            data = data.replace(char, '')
        
        # Limit length
        if len(data) > max_length:
            data = data[:max_length]
        
        # Handle unicode
        if not allow_unicode:
            data = data.encode('ascii', errors='ignore').decode('ascii')
        
        return data.strip()


class PathValidator:
    """Safe path handling utilities"""
    
    @classmethod
    def safe_path_join(cls, base_path: Path, user_path: str) -> Path:
        """Safely join paths and prevent directory traversal"""
        base = Path(base_path).resolve()
        
        # Sanitize user path
        user_path = user_path.strip()
        user_path = user_path.replace('\\', '/')  # Normalize separators
        
        # Remove dangerous path components
        dangerous_components = ['..', '.', '~', '$']
        path_parts = [part for part in user_path.split('/') if part and part not in dangerous_components]
        
        if not path_parts:
            raise SecurityError("Invalid path")
        
        # Join with base path
        full_path = base
        for part in path_parts:
            # Additional validation on each part
            if any(char in part for char in ['<', '>', ':', '"', '|', '?', '*', '\0']):
                raise SecurityError(f"Invalid path component: {part}")
            full_path = full_path / part
        
        # Ensure the final path is within the base directory
        try:
            full_path = full_path.resolve()
            if not str(full_path).startswith(str(base)):
                raise SecurityError("Path traversal attempt detected")
        except (OSError, ValueError) as e:
            raise SecurityError(f"Path resolution failed: {e}")
        
        return full_path
    
    @classmethod
    def validate_filename(cls, filename: str) -> bool:
        """Validate filename security"""
        if not isinstance(filename, str):
            return False
        
        if not filename or len(filename) > 255:
            return False
        
        # Check for reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        
        if filename.upper() in reserved_names:
            return False
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0', '/', '\\']
        if any(char in filename for char in dangerous_chars):
            return False
        
        return True


class RateLimiter:
    """Rate limiting utility for preventing abuse"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed under rate limit"""
        current_time = time.time()
        
        # Initialize if first request
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < self.window_seconds
        ]
        
        # Check rate limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(current_time)
        return True
    
    def cleanup(self):
        """Clean up old entries"""
        current_time = time.time()
        
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if current_time - req_time < self.window_seconds
            ]
            
            if not self.requests[identifier]:
                del self.requests[identifier]


class CryptoUtils:
    """Cryptographic utilities"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate a secure random password"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def hash_string(data: str, salt: Optional[str] = None) -> str:
        """Hash string with optional salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        combined = f"{salt}:{data}"
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return f"{salt}:{hash_obj.hexdigest()}"
    
    @staticmethod
    def verify_hash(data: str, hashed: str) -> bool:
        """Verify string against hash"""
        try:
            salt, hash_value = hashed.split(':', 1)
            combined = f"{salt}:{data}"
            hash_obj = hashlib.sha256(combined.encode('utf-8'))
            return hash_obj.hexdigest() == hash_value
        except ValueError:
            return False


class SecurityContext:
    """Security context for request validation"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.blocked_ips: Dict[str, datetime] = {}
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS
            r'union\s+select',  # SQL injection
            r'javascript:',  # JavaScript injection
            r'data:text/html',  # Data URI XSS
        ]
    
    def validate_request(self, source_ip: str, data: Dict[str, Any]) -> bool:
        """Validate incoming request"""
        # Check if IP is blocked
        if source_ip in self.blocked_ips:
            if datetime.now() - self.blocked_ips[source_ip] < timedelta(hours=1):
                return False
            else:
                del self.blocked_ips[source_ip]
        
        # Check rate limit
        if not self.rate_limiter.is_allowed(source_ip):
            logger.warning(f"Rate limit exceeded for IP: {source_ip}")
            return False
        
        # Check for suspicious patterns
        for key, value in data.items():
            if isinstance(value, str):
                for pattern in self.suspicious_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        logger.warning(f"Suspicious pattern detected from {source_ip}: {pattern}")
                        self.block_ip(source_ip)
                        return False
        
        return True
    
    def block_ip(self, ip: str):
        """Block IP address temporarily"""
        self.blocked_ips[ip] = datetime.now()
        logger.warning(f"Blocked IP address: {ip}")


# Global security context
security_context = SecurityContext()


def validate_proxy_config(config: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate proxy configuration"""
    required_fields = ['server', 'port', 'protocol']
    
    for field in required_fields:
        if field not in config:
            return False, f"Missing required field: {field}"
    
    # Validate server
    if not InputValidator.validate_server_address(config['server']):
        return False, "Invalid server address"
    
    # Validate port
    if not InputValidator.validate_port(config['port']):
        return False, "Invalid port number"
    
    # Validate protocol
    allowed_protocols = ['vless', 'trojan', 'shadowsocks', 'vmess']
    if config['protocol'] not in allowed_protocols:
        return False, f"Unsupported protocol: {config['protocol']}"
    
    # Protocol-specific validation
    if config['protocol'] == 'vless' and 'uuid' in config:
        if not InputValidator.validate_uuid(config['uuid']):
            return False, "Invalid UUID format"
    
    if config['protocol'] == 'trojan' and 'password' in config:
        if not InputValidator.validate_password(config['password']):
            return False, "Invalid password format"
    
    return True, "Configuration is valid"


def sanitize_log_message(message: str) -> str:
    """Sanitize log message to prevent log injection"""
    if not isinstance(message, str):
        message = str(message)
    
    # Remove newlines and carriage returns
    message = message.replace('\n', '\\n').replace('\r', '\\r')
    
    # Remove null bytes
    message = message.replace('\0', '\\0')
    
    # Limit length
    if len(message) > 1000:
        message = message[:997] + "..."
    
    return message
