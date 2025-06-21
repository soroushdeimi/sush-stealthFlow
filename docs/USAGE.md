# StealthFlow Usage Guide

## Day-to-Day Usage

### Managing Your Server

Once installed, StealthFlow runs as a system service. Here's what you need to know:

```bash
# Check if everything's running
sudo systemctl status stealthflow

# Tail the logs (useful for debugging)
sudo journalctl -u stealthflow -f

# Restart if needed
sudo systemctl restart stealthflow

# Get server info and client configs
sudo stealthflow-admin info

# Add a new user
sudo stealthflow-admin add-user username

# Check server health
curl -s http://localhost:9000/health
```

### Using the Client

**GUI Mode (Recommended for beginners)**
The GUI shows connection status, lets you switch between profiles, and displays real-time speed/latency stats.

```bash
python stealthflow.py gui
```

**CLI Mode (For automation/scripting)**
```bash
# Basic connection
python stealthflow.py cli

# Connect with specific profile
python stealthflow.py cli --profile "My Server"

# List all profiles
python stealthflow.py cli --list

# Test connection speed
python stealthflow.py cli --speed-test

# Run in background
python stealthflow.py cli --daemon

# Check status
python stealthflow.py cli --status
```

**Profile Management**
```bash
# Add new server
python stealthflow.py profile add \
  --name "My Server" \
  --server example.com \
  --port 443 \
  --protocol reality \
  --uuid "your-uuid-here"

# Edit existing profile
python stealthflow.py profile edit "My Server" --port 8443

# Remove profile
python stealthflow.py profile remove "My Server"

# Import from server
python stealthflow.py profile import --server example.com --key your-import-key

# Export for sharing
python stealthflow.py profile export "My Server" --output my-config.json
```

### Advanced Features

**P2P Fallback Network**
When traditional proxies fail, StealthFlow can connect you through other users:

```bash
# Start P2P signaling server (usually runs on your VPS)
python stealthflow.py p2p-server --port 8765

# Connect client with P2P fallback enabled
python stealthflow.py cli --enable-p2p

# Force P2P mode (useful for testing)
python stealthflow.py cli --p2p-only
```

**Monitoring and Health Checks**
```bash
# Enable monitoring stack (Prometheus + Grafana)
docker-compose -f docker-compose.monitoring.yml up -d

# Access dashboards:
# Grafana: http://localhost:3000 (admin/your-password)
# Prometheus: http://localhost:9090

# Manual health check
python stealthflow.py health-check --all-profiles
```

**Using with Other Apps**
StealthFlow creates local SOCKS5 and HTTP proxies that work with any app:

```bash
# Default ports:
# SOCKS5: 127.0.0.1:10808
# HTTP: 127.0.0.1:10809

# Examples:
curl --proxy socks5://127.0.0.1:10808 https://ipinfo.io
firefox --proxy-server="socks5://127.0.0.1:10808"
git config --global http.proxy http://127.0.0.1:10809
```
