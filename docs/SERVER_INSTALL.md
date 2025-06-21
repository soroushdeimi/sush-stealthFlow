# StealthFlow Server Installation Guide

A comprehensive guide to installing and configuring StealthFlow server on various platforms.

## Prerequisites

### System Requirements
- **Operating System**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+ / RHEL 8+
- **Memory**: Minimum 1 GB RAM (2 GB recommended)
- **Storage**: Minimum 10 GB free space
- **Privileges**: Root or sudo access
- **Architecture**: x86_64 (AMD64)

### Network Requirements
- VPS server with public IP address
- Domain name (for SSL/TLS certificate)
- DNS management access
- Open ports: 80 (HTTP), 443 (HTTPS), 8080 (Management)
- Stable internet connection

### Optional Components
- CDN account (Cloudflare, AWS CloudFront, etc.)
- Domain registrar with API access
- Monitoring service integration
- Backup storage solution

## Quick Installation (Recommended)

### One-Line Installation
```bash
# Download and execute the automated installer
curl -sSL https://raw.githubusercontent.com/stealthflow/stealthflow/main/server/scripts/install.sh | bash
```

### Docker Installation
```bash
# Clone the repository
git clone https://github.com/stealthflow/stealthflow.git
cd stealthflow

# Start with Docker Compose
docker-compose up -d
```

## Manual Installation

### Step 1: System Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential dependencies
sudo apt install -y \
    curl \
    wget \
    unzip \
    nginx \
    certbot \
    python3-certbot-nginx \
    ufw \
    htop \
    git \
    build-essential

# Install Python dependencies
sudo apt install -y python3 python3-pip python3-venv
```

### Step 2: Install Xray-core

```bash
# Get latest Xray version
XRAY_VERSION=$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases/latest | grep tag_name | cut -d '"' -f 4)

# Download Xray binary
wget "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/Xray-linux-64.zip"

# Extract and install
unzip Xray-linux-64.zip
sudo mv xray /usr/local/bin/
sudo chmod +x /usr/local/bin/xray

# Verify installation
xray version
```

### Step 3: Create System User

```bash
# Create dedicated user for StealthFlow
sudo useradd -r -s /bin/false stealthflow
sudo mkdir -p /etc/stealthflow
sudo mkdir -p /var/log/stealthflow
sudo mkdir -p /var/lib/stealthflow

# Set permissions
sudo chown -R stealthflow:stealthflow /etc/stealthflow
sudo chown -R stealthflow:stealthflow /var/log/stealthflow
sudo chown -R stealthflow:stealthflow /var/lib/stealthflow
```

### Step 4: Install StealthFlow

```bash
# Clone StealthFlow repository
git clone https://github.com/stealthflow/stealthflow.git /opt/stealthflow
cd /opt/stealthflow

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Set ownership
sudo chown -R stealthflow:stealthflow /opt/stealthflow
```

### Step 5: Configure Services

```bash
# Copy configuration files
sudo cp server/config/stealthflow.conf /etc/stealthflow/
sudo cp server/config/xray.json /etc/stealthflow/

# Copy systemd service files
sudo cp server/systemd/stealthflow.service /etc/systemd/system/
sudo cp server/systemd/xray.service /etc/systemd/system/

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable stealthflow
sudo systemctl enable xray
```

### Step 6: Configure Nginx

```bash
# Copy Nginx configuration
sudo cp server/nginx/stealthflow.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/stealthflow.conf /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 7: SSL Certificate Setup

```bash
# Obtain SSL certificate with Certbot (replace your-domain.com)
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Set up automatic renewal
sudo systemctl enable certbot.timer
```

### Step 8: Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp
sudo ufw --force enable
```

### Step 9: Start Services

```bash
# Start and verify services
sudo systemctl start xray
sudo systemctl start stealthflow

# Check service status
sudo systemctl status xray
sudo systemctl status stealthflow

# View logs
sudo journalctl -u stealthflow -f
```

## Configuration

### Basic Configuration

Edit `/etc/stealthflow/stealthflow.conf`:

```ini
[server]
host = 0.0.0.0
port = 8080
domain = your-domain.com
ssl_cert = /etc/letsencrypt/live/your-domain.com/fullchain.pem
ssl_key = /etc/letsencrypt/live/your-domain.com/privkey.pem

[proxy]
xray_config = /etc/stealthflow/xray.json
fallback_port = 80

[security]
enable_auth = true
api_key = your-secure-api-key-here
rate_limit = 100

[logging]
level = INFO
file = /var/log/stealthflow/server.log
max_size = 10MB
backup_count = 5
```

## Troubleshooting

### Common Issues

1. **Service fails to start**
   ```bash
   sudo journalctl -u stealthflow --no-pager -l
   sudo systemctl status stealthflow
   ```

2. **SSL certificate issues**
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

3. **Port conflicts**
   ```bash
   sudo netstat -tlnp | grep :443
   sudo ss -tulpn | grep :443
   ```

4. **Permission issues**
   ```bash
   sudo chown -R stealthflow:stealthflow /opt/stealthflow
   sudo chmod -R 755 /opt/stealthflow
   ```

### Health Checks

```bash
# Check service health
curl -k https://your-domain.com/health

# Monitor system resources
htop

# Check logs
tail -f /var/log/stealthflow/server.log
```

## Security Hardening

### SSH Hardening
```bash
# Edit SSH configuration
sudo nano /etc/ssh/sshd_config

# Recommended settings:
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes
# Port 2222 (change default port)

sudo systemctl restart ssh
```

### Additional Security
```bash
# Install fail2ban
sudo apt install -y fail2ban

# Configure fail2ban for StealthFlow
sudo tee /etc/fail2ban/jail.local << EOF
[stealthflow]
enabled = true
port = 8080
protocol = tcp
filter = stealthflow
logpath = /var/log/stealthflow/server.log
maxretry = 5
bantime = 3600
findtime = 600
EOF

sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.
