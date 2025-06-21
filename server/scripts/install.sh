#!/bin/bash

# StealthFlow Server Installation Script
# Automated server installation with all components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logo
echo -e "${BLUE}
███████╗████████╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗███████╗██╗      ██████╗ ██╗    ██╗
██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║██╔════╝██║     ██╔═══██╗██║    ██║
███████╗   ██║   █████╗  ███████║██║     ██║   ███████║█████╗  ██║     ██║   ██║██║ █╗ ██║
╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██║   ██╔══██║██╔══╝  ██║     ██║   ██║██║███╗██║
███████║   ██║   ███████╗██║  ██║███████╗██║   ██║  ██║██║     ███████╗╚██████╔╝╚███╔███╔╝
╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝ 
${NC}"

echo -e "${GREEN}=== StealthFlow Server Installer ===${NC}"
echo -e "${YELLOW}Installing multi-protocol proxy with REALITY, Trojan, and Multi-CDN support${NC}"
echo

# Check root access
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   exit 1
fi

# Configuration variables
DOMAIN=""
EMAIL=""
UUID=""
TROJAN_PASSWORD=""
REALITY_PRIVATE_KEY=""
REALITY_SHORT_ID=""

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Generate UUID
generate_uuid() {
    if command -v uuidgen &> /dev/null; then
        uuidgen
    else
        cat /proc/sys/kernel/random/uuid
    fi
}

# Generate strong password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Get information from user
get_user_input() {
    echo -e "${BLUE}=== Configuration Setup ===${NC}"
    
    read -p "Enter your domain (e.g., yourdomain.com): " DOMAIN
    if [[ -z "$DOMAIN" ]]; then
        log_error "Domain cannot be empty"
        exit 1
    fi
    
    read -p "Enter your email for SSL certificates: " EMAIL
    if [[ -z "$EMAIL" ]]; then
        log_error "Email cannot be empty"
        exit 1
    fi
    
    # Auto-generate UUID and passwords
    UUID=$(generate_uuid)
    TROJAN_PASSWORD=$(generate_password)
    
    log_info "Generated UUID: $UUID"
    log_info "Generated Trojan password: $TROJAN_PASSWORD"
    
    echo
}

# Update system
update_system() {
    log_info "Updating system packages..."
    
    if command -v apt &> /dev/null; then
        export DEBIAN_FRONTEND=noninteractive
        apt update -y
        apt upgrade -y
        apt install -y curl wget unzip nginx certbot python3-certbot-nginx ufw
    elif command -v yum &> /dev/null; then
        yum update -y
        yum install -y curl wget unzip nginx certbot python3-certbot-nginx firewalld
    else
        log_error "Unsupported package manager"
        exit 1
    fi
}

# Install Xray-core
install_xray() {
    log_info "Installing Xray-core..."
    
    # Download latest Xray version
    XRAY_VERSION=$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases/latest | grep -o '"tag_name": *"[^"]*"' | cut -d'"' -f4)
    
    if [[ -z "$XRAY_VERSION" ]]; then
        log_error "Failed to get Xray version"
        exit 1
    fi
    
    log_info "Downloading Xray $XRAY_VERSION..."
    
    # Detect architecture
    ARCH=$(uname -m)
    case $ARCH in
        x86_64) XRAY_ARCH="64" ;;
        aarch64|arm64) XRAY_ARCH="arm64-v8a" ;;
        armv7l) XRAY_ARCH="arm32-v7a" ;;
        *) log_error "Unsupported architecture: $ARCH"; exit 1 ;;
    esac
    
    # Download and install
    cd /tmp
    wget "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/Xray-linux-${XRAY_ARCH}.zip"
    unzip -o "Xray-linux-${XRAY_ARCH}.zip"
    
    # Install files
    mkdir -p /usr/local/bin /etc/xray /var/log/xray
    mv xray /usr/local/bin/
    chmod +x /usr/local/bin/xray
    
    # Create xray user
    useradd -r -s /usr/sbin/nologin xray || true
    
    # Create systemd service
    cat > /etc/systemd/system/xray.service << EOF
[Unit]
Description=Xray Service
Documentation=https://github.com/xtls
After=network.target nss-lookup.target

[Service]
User=xray
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ExecStart=/usr/local/bin/xray run -config /etc/xray/config.json
Restart=on-failure
RestartPreventExitStatus=23
LimitNPROC=10000
LimitNOFILE=1000000

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable xray
    
    log_info "Xray installed successfully"
}

# Generate REALITY keys
generate_reality_keys() {
    log_info "Generating REALITY keys..."
    
    # Use Xray to generate keys
    REALITY_KEYS=$(/usr/local/bin/xray x25519)
    REALITY_PRIVATE_KEY=$(echo "$REALITY_KEYS" | grep "Private key:" | cut -d' ' -f3)
    REALITY_PUBLIC_KEY=$(echo "$REALITY_KEYS" | grep "Public key:" | cut -d' ' -f3)
    
    # Generate Short ID
    REALITY_SHORT_ID=$(openssl rand -hex 8)
    
    log_info "REALITY Private Key: $REALITY_PRIVATE_KEY"
    log_info "REALITY Public Key: $REALITY_PUBLIC_KEY"
    log_info "REALITY Short ID: $REALITY_SHORT_ID"
}

# Configure Xray
configure_xray() {
    log_info "Configuring Xray..."
    
    cat > /etc/xray/config.json << EOF
{
  "log": {
    "access": "/var/log/xray/access.log",
    "error": "/var/log/xray/error.log",
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "tag": "vless-reality",
      "listen": "0.0.0.0",
      "port": 444,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "$UUID",
            "flow": "xtls-rprx-vision",
            "email": "reality@stealthflow.local"
          }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "show": false,
          "dest": "www.microsoft.com:443",
          "xver": 0,
          "serverNames": [
            "cdn1.$DOMAIN",
            "cdn2.$DOMAIN", 
            "cdn3.$DOMAIN"
          ],
          "privateKey": "$REALITY_PRIVATE_KEY",
          "shortIds": ["$REALITY_SHORT_ID"]
        }
      },
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls"]
      }
    },
    {
      "tag": "trojan-cdn",
      "listen": "127.0.0.1",
      "port": 8443,
      "protocol": "trojan",
      "settings": {
        "clients": [
          {
            "password": "$TROJAN_PASSWORD",
            "email": "trojan@stealthflow.local"
          }
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {
          "alpn": ["h2", "http/1.1"],
          "certificates": [
            {
              "certificateFile": "/etc/letsencrypt/live/$DOMAIN/fullchain.pem",
              "keyFile": "/etc/letsencrypt/live/$DOMAIN/privkey.pem"
            }
          ]
        }
      },
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls"]
      }
    }
  ],
  "outbounds": [
    {
      "tag": "direct",
      "protocol": "freedom",
      "settings": {
        "domainStrategy": "UseIPv4"
      }
    },
    {
      "tag": "block",
      "protocol": "blackhole",
      "settings": {
        "response": {
          "type": "http"
        }
      }
    }
  ],
  "routing": {
    "domainStrategy": "IPIfNonMatch",
    "rules": [
      {
        "type": "field",
        "ip": ["geoip:private"],
        "outboundTag": "direct"
      },
      {
        "type": "field",
        "domain": ["geosite:category-ads-all"],
        "outboundTag": "block"
      }
    ]
  }
}
EOF

    chown xray:xray /etc/xray/config.json
    chmod 600 /etc/xray/config.json
}

# Get SSL certificate
setup_ssl() {
    log_info "Setting up SSL certificates..."
    
    # Stop nginx temporarily
    systemctl stop nginx || true
    
    # Get certificate for main domain and subdomains
    certbot certonly --standalone --email "$EMAIL" --agree-tos --no-eff-email \
        -d "$DOMAIN" \
        -d "cdn1.$DOMAIN" \
        -d "cdn2.$DOMAIN" \
        -d "cdn3.$DOMAIN"
    
    # Setup automatic renewal
    echo "0 2 * * * root certbot renew --quiet && systemctl reload nginx" >> /etc/crontab
}

# Configure Nginx
configure_nginx() {
    log_info "Configuring Nginx..."
    
    # Backup existing config
    cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup || true
    
    cat > /etc/nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

stream {
    map $ssl_preread_server_name $backend {
        ~^cdn[1-3]\..*$ 127.0.0.1:8443;
        default 127.0.0.1:444;
    }

    server {
        listen 443;
        listen [::]:443;
        proxy_pass $backend;
        ssl_preread on;
        proxy_protocol off;
    }
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    server_tokens off;
    
    server {
        listen 80;
        server_name _;
        return 301 https://$server_name$request_uri;
    }
}
EOF

    # Test config
    nginx -t
    
    systemctl enable nginx
    systemctl restart nginx
}

# Configure firewall
setup_firewall() {
    log_info "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        ufw --force reset
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow ssh
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw --force enable
    elif command -v firewall-cmd &> /dev/null; then
        systemctl enable firewalld
        systemctl start firewalld
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
    fi
}

# Create client files
generate_client_configs() {
    log_info "Generating client configurations..."
    
    mkdir -p /root/stealthflow-configs
    
    # REALITY config
    cat > /root/stealthflow-configs/reality.json << EOF
{
  "remarks": "StealthFlow-REALITY",
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "tag": "socks",
      "port": 10808,
      "listen": "127.0.0.1",
      "protocol": "socks",
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls"]
      },
      "settings": {
        "auth": "noauth",
        "udp": true
      }
    },
    {
      "tag": "http",
      "port": 10809,
      "listen": "127.0.0.1",
      "protocol": "http",
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls"]
      }
    }
  ],
  "outbounds": [
    {
      "tag": "proxy",
      "protocol": "vless",
      "settings": {
        "vnext": [
          {
            "address": "YOUR_SERVER_IP",
            "port": 443,
            "users": [
              {
                "id": "$UUID",
                "encryption": "none",
                "flow": "xtls-rprx-vision"
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "serverName": "www.microsoft.com",
          "fingerprint": "chrome",
          "show": false,
          "publicKey": "$REALITY_PUBLIC_KEY",
          "shortId": "$REALITY_SHORT_ID",
          "spiderX": "/"
        }
      }
    },
    {
      "tag": "direct",
      "protocol": "freedom",
      "settings": {}
    },
    {
      "tag": "block",
      "protocol": "blackhole",
      "settings": {
        "response": {
          "type": "http"
        }
      }
    }
  ],
  "routing": {
    "domainStrategy": "IPIfNonMatch",
    "rules": [
      {
        "type": "field",
        "ip": ["geoip:private"],
        "outboundTag": "direct"
      },
      {
        "type": "field",
        "domain": ["geosite:category-ads-all"],
        "outboundTag": "block"
      }
    ]
  }
}
EOF

    # Trojan config
    cat > /root/stealthflow-configs/trojan-cdn1.json << EOF
{
  "remarks": "StealthFlow-Trojan-CDN1",
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "tag": "socks",
      "port": 10808,
      "listen": "127.0.0.1",
      "protocol": "socks",
      "sniffing": {
        "enabled": true,
        "destOverride": ["http", "tls"]
      },
      "settings": {
        "auth": "noauth",
        "udp": true
      }
    }
  ],
  "outbounds": [
    {
      "tag": "proxy",
      "protocol": "trojan",
      "settings": {
        "servers": [
          {
            "address": "cdn1.$DOMAIN",
            "port": 443,
            "password": "$TROJAN_PASSWORD"
          }
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "tls",
        "tlsSettings": {
          "allowInsecure": false,
          "serverName": "cdn1.$DOMAIN"
        }
      }
    },
    {
      "tag": "direct",
      "protocol": "freedom"
    }
  ],
  "routing": {
    "rules": [
      {
        "type": "field",
        "ip": ["geoip:private"],
        "outboundTag": "direct"
      }
    ]
  }
}
EOF

    # Create subscription URLs
    REALITY_URL="vless://$UUID@YOUR_SERVER_IP:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.microsoft.com&fp=chrome&pbk=$REALITY_PUBLIC_KEY&sid=$REALITY_SHORT_ID&type=tcp&headerType=none#StealthFlow-REALITY"
    TROJAN_URL="trojan://$TROJAN_PASSWORD@cdn1.$DOMAIN:443?security=tls&type=tcp&headerType=none&sni=cdn1.$DOMAIN#StealthFlow-Trojan-CDN1"
    
    cat > /root/stealthflow-configs/share-urls.txt << EOF
StealthFlow Configuration URLs:

REALITY (Direct):
$REALITY_URL

Trojan (CDN1):
$TROJAN_URL

Replace YOUR_SERVER_IP with your actual server IP address.
EOF

    log_info "Client configurations saved to /root/stealthflow-configs/"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    systemctl restart nginx
    systemctl restart xray
    
    # Check service status
    if systemctl is-active --quiet nginx; then
        log_info "Nginx is running"
    else
        log_error "Nginx failed to start"
    fi
    
    if systemctl is-active --quiet xray; then
        log_info "Xray is running"
    else
        log_error "Xray failed to start"
    fi
}

# Display final information
show_final_info() {
    echo
    echo -e "${GREEN}=== Installation Complete! ===${NC}"
    echo
    echo -e "${YELLOW}Server Information:${NC}"
    echo "Domain: $DOMAIN"
    echo "Server IP: $(curl -s ipv4.icanhazip.com || echo 'Unknown')"
    echo
    echo -e "${YELLOW}REALITY Configuration:${NC}"
    echo "UUID: $UUID"
    echo "Private Key: $REALITY_PRIVATE_KEY"
    echo "Public Key: $REALITY_PUBLIC_KEY"
    echo "Short ID: $REALITY_SHORT_ID"
    echo
    echo -e "${YELLOW}Trojan Configuration:${NC}"
    echo "Password: $TROJAN_PASSWORD"
    echo
    echo -e "${YELLOW}Client configurations saved to:${NC}"
    echo "/root/stealthflow-configs/"
    echo
    echo -e "${BLUE}Replace YOUR_SERVER_IP in client configs with your actual server IP!${NC}"
    echo
    echo -e "${GREEN}StealthFlow server is now ready!${NC}"
}

# Main execution
main() {
    get_user_input
    update_system
    install_xray
    generate_reality_keys
    configure_xray
    setup_ssl
    configure_nginx
    setup_firewall
    generate_client_configs
    start_services
    show_final_info
}

# Execute
main "$@"
