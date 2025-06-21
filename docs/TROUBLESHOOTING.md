# StealthFlow Troubleshooting Guide

## Server-side Issues

### Check Service Status
```bash
# Check if services are running
sudo systemctl status stealthflow nginx

# Check certificate status
sudo certbot certificates

# Test configuration
sudo xray test -config /etc/xray/config.json

# Check firewall
sudo ufw status

# View detailed logs
sudo journalctl -u stealthflow -f --since "1 hour ago"
```

### Common Server Problems

**Service won't start**
```bash
# Check system logs
sudo journalctl -u stealthflow --no-pager

# Verify configuration syntax
sudo xray test -config /etc/xray/config.json

# Check file permissions
sudo ls -la /etc/xray/
```

**Certificate issues**
```bash
# Renew certificates manually
sudo certbot renew

# Check certificate validity
sudo certbot certificates

# Verify domain DNS
nslookup yourdomain.com
```

## Client-side Issues

### Basic Diagnostics
```bash
# Test basic connectivity
python stealthflow.py cli --test

# Check profile configuration
python stealthflow.py profile validate "My Server"

# Reset to defaults
python stealthflow.py reset --keep-profiles

# Enable debug logging
python stealthflow.py cli --debug --log-file debug.log
```

### Connection Problems

**Can't connect to server**
```bash
# Test server connectivity
telnet your-server-ip 443

# Check DNS resolution
nslookup yourdomain.com

# Test with curl
curl -v https://yourdomain.com
```

**Slow connections**
```bash
# Test speed with different profiles
python stealthflow.py cli --speed-test

# Check local proxy
curl --proxy socks5://127.0.0.1:10808 https://ipinfo.io

# Monitor connection quality
python stealthflow.py cli --monitor
```

## Network Diagnostic Commands

### Port Testing
```bash
# Test if ports are open
nmap -p 443,80 your-server-ip

# Check specific port
nc -zv your-server-ip 443
```

### Traffic Analysis
```bash
# Monitor network traffic (Linux)
sudo tcpdump -i any -n host your-server-ip

# Check local proxy traffic
ss -tlnp | grep :10808
```

### DNS Issues
```bash
# Check DNS resolution
dig yourdomain.com
nslookup yourdomain.com 8.8.8.8

# Flush DNS cache (varies by OS)
# Linux: sudo systemctl restart systemd-resolved
# macOS: sudo dscacheutil -flushcache
# Windows: ipconfig /flushdns
```

## Performance Issues

### Server Optimization
```bash
# Check system resources
htop
df -h
free -h

# Monitor Xray processes
ps aux | grep xray

# Check network limits
ulimit -n
```

### Client Optimization
```bash
# Check Python performance
python -m cProfile stealthflow.py cli --profile "My Server"

# Monitor memory usage
python -m memory_profiler stealthflow.py cli
```

## Logging and Debugging

### Server Logs
```bash
# Xray logs
sudo tail -f /var/log/xray/access.log
sudo tail -f /var/log/xray/error.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u stealthflow -f
```

### Client Logs
```bash
# Enable verbose logging
python stealthflow.py cli --verbose --log-file client.log

# Check specific component logs
python stealthflow.py cli --debug-component health_checker
```

## Emergency Recovery

### Server Recovery
```bash
# Stop all services
sudo systemctl stop stealthflow nginx

# Backup current config
sudo cp -r /etc/xray /etc/xray.backup

# Restore from backup
sudo cp -r /etc/xray.backup /etc/xray

# Restart services
sudo systemctl start stealthflow nginx
```

### Client Recovery
```bash
# Reset client configuration
python stealthflow.py reset --full

# Reimport profiles
python stealthflow.py profile import --from-backup
```

## Getting Help

If these steps don't resolve your issue:

1. Enable debug logging and collect logs
2. Check [GitHub Issues](https://github.com/soroushdeimi/sush-stealthFlow/issues)
3. Create a new issue with:
   - OS and version
   - StealthFlow version
   - Error messages
   - Steps to reproduce
   - Debug logs (without sensitive info)
