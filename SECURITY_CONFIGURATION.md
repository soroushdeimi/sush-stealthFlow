# StealthFlow Security Configuration Guide

## Overview

StealthFlow has been enhanced with comprehensive security measures to protect against various attack vectors and ensure safe operation in hostile network environments.

## Security Features

### 1. Input Validation and Sanitization

All user inputs are now validated and sanitized using the security module (`utils/security.py`):

- **Server Address Validation**: Validates IP addresses and domain names
- **Port Validation**: Ensures ports are within valid range (1-65535)
- **UUID Validation**: Validates UUID format for VLESS protocols
- **Password Validation**: Ensures minimum security requirements
- **String Sanitization**: Removes dangerous characters and limits lengths

### 2. P2P Authentication System

The P2P signaling server now includes:

- **Peer Authentication**: Challenge-response authentication for all peers
- **Reputation System**: Tracks peer behavior and blocks malicious actors
- **Trust Verification**: Only allows connections between trusted peers
- **Rate Limiting**: Prevents abuse and DoS attacks

### 3. Network Security

Enhanced network security measures:

- **Connection Rate Limiting**: Limits new connections per IP
- **Message Rate Limiting**: Prevents message flooding
- **Message Size Limits**: Prevents oversized message attacks
- **Secure WebSocket Configuration**: Proper timeouts and queue limits

### 4. Path Security

File system protection:

- **Path Traversal Prevention**: Validates all file paths
- **Safe Path Joining**: Prevents directory traversal attacks
- **Filename Validation**: Blocks dangerous filename patterns

## Configuration

### Security Module Configuration

The security module provides several configurable components:

```python
from utils.security import SecurityContext, RateLimiter, InputValidator

# Rate limiting configuration
rate_limiter = RateLimiter(
    max_requests=100,    # Maximum requests per window
    window_seconds=60    # Time window in seconds
)

# Security context for request validation
security_context = SecurityContext()
```

### P2P Security Configuration

P2P signaling server security settings:

```python
class SignalingServer:
    def __init__(self):
        # Connection rate limiting
        self.connection_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        # Message rate limiting
        self.rate_limiter = RateLimiter(max_requests=50, window_seconds=60)
        
        # WebSocket configuration
        max_size=8192        # Maximum message size
        max_queue=32         # Maximum connection queue
        ping_interval=30     # Ping interval
        ping_timeout=10      # Ping timeout
```

### Input Validation Examples

```python
from utils.security import InputValidator

# Validate server address
if InputValidator.validate_server_address("example.com"):
    print("Valid server address")

# Validate port
if InputValidator.validate_port(8080):
    print("Valid port")

# Validate UUID
if InputValidator.validate_uuid("550e8400-e29b-41d4-a716-446655440000"):
    print("Valid UUID")

# Sanitize user input
sanitized = InputValidator.sanitize_string(user_input, max_length=100)
```

## Best Practices

### 1. Server Configuration

- **Change Default Passwords**: Never use placeholder passwords
- **Use Strong Authentication**: Implement proper key management
- **Enable Rate Limiting**: Configure appropriate limits for your use case
- **Monitor Logs**: Regularly check for security violations

### 2. Client Configuration

- **Validate All Inputs**: Use the security module for all user inputs
- **Secure Storage**: Don't store sensitive data in plain text
- **Regular Updates**: Keep security configurations updated

### 3. P2P Networks

- **Trust Verification**: Only connect to authenticated peers
- **Reputation Monitoring**: Track and block malicious peers
- **Connection Limits**: Limit concurrent P2P connections

## Security Incidents

### Handling Security Violations

When security violations are detected:

1. **Automatic Blocking**: Malicious IPs are temporarily blocked
2. **Reputation Reduction**: Peer reputation scores are decreased
3. **Logging**: All security events are logged for analysis
4. **Rate Limiting**: Aggressive rate limiting is applied

### Monitoring and Alerting

Monitor these security metrics:

- `stats["security_violations"]`: Number of security violations
- `stats["rejected_connections"]`: Rejected connections due to rate limiting
- Peer reputation scores below 30
- Unusual message patterns or volumes

## Advanced Security Features

### 1. Cryptographic Utilities

```python
from utils.security import CryptoUtils

# Generate secure tokens
token = CryptoUtils.generate_secure_token(32)

# Generate secure passwords
password = CryptoUtils.generate_secure_password(16)

# Hash strings securely
hashed = CryptoUtils.hash_string("sensitive_data")

# Verify hashes
if CryptoUtils.verify_hash("sensitive_data", hashed):
    print("Hash verified")
```

### 2. Security Context

```python
from utils.security import security_context

# Validate incoming requests
if security_context.validate_request(client_ip, request_data):
    process_request(request_data)
else:
    reject_request("Security validation failed")
```

### 3. Log Sanitization

```python
from utils.security import sanitize_log_message

# Safely log user data
logger.info(sanitize_log_message(f"User input: {user_data}"))
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the security module is in the correct path
2. **Rate Limiting**: Adjust rate limits if legitimate traffic is blocked
3. **Authentication Failures**: Check peer authentication configuration
4. **Input Validation**: Verify input format requirements

### Error Messages

- `"Security validation failed"`: Input failed security checks
- `"Rate limit exceeded"`: Too many requests in time window
- `"Authentication required"`: Peer needs to authenticate first
- `"Path traversal attempt detected"`: Dangerous file path detected

### Performance Considerations

- Rate limiting uses memory proportional to unique identifiers
- Input validation adds small computational overhead
- P2P authentication requires additional round trips
- Regular cleanup prevents memory leaks

## Security Updates

This security framework provides:

- **Prevention**: Input validation and sanitization
- **Detection**: Security violation monitoring
- **Response**: Automatic blocking and rate limiting
- **Recovery**: Reputation-based trust management

Regular security audits and updates are recommended to maintain effectiveness against evolving threats.
