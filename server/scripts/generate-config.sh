#!/bin/bash

# StealthFlow Configuration Generator
# Configuration generator for StealthFlow server

set -e

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[CONFIG]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[CONFIG]${NC} $1"
}

log_error() {
    echo -e "${RED}[CONFIG]${NC} $1"
}

# Generate REALITY keys
generate_reality_keys() {
    log_info "Generating REALITY keys..."
    
    if command -v xray &> /dev/null; then
        REALITY_KEYS=$(xray x25519)
        REALITY_PRIVATE_KEY=$(echo "$REALITY_KEYS" | grep "Private key:" | cut -d' ' -f3)
        REALITY_PUBLIC_KEY=$(echo "$REALITY_KEYS" | grep "Public key:" | cut -d' ' -f3)
    else
        log_error "Xray not found, cannot generate REALITY keys"
        exit 1
    fi
    
    REALITY_SHORT_ID=$(openssl rand -hex 8)
    
    log_info "REALITY keys generated successfully"
}

# Generate UUID
generate_uuid() {
    if command -v uuidgen &> /dev/null; then
        UUID=$(uuidgen)
    else
        UUID=$(cat /proc/sys/kernel/random/uuid)
    fi
    log_info "Generated UUID: $UUID"
}

# Generate Trojan password
generate_trojan_password() {
    TROJAN_PASSWORD=$(openssl rand -base64 32)
    log_info "Generated Trojan password"
}

# Generate Xray config
generate_xray_config() {
    log_info "Generating Xray configuration..."
    
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
            "${DOMAIN}",
            "cdn1.${DOMAIN}",
            "cdn2.${DOMAIN}",
            "cdn3.${DOMAIN}"
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
              "certificateFile": "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem",
              "keyFile": "/etc/letsencrypt/live/${DOMAIN}/privkey.pem"
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

# Generate Nginx configuration
generate_nginx_config() {
    log_info "Generating Nginx configuration..."
    
    cat > /etc/nginx/nginx.conf << EOF
events {
    worker_connections 1024;
}

stream {
    map \$ssl_preread_server_name \$backend {
        ~^cdn[1-3]\..*\$ 127.0.0.1:8443;
        default 127.0.0.1:444;
    }

    server {
        listen 443;
        listen [::]:443;
        proxy_pass \$backend;
        ssl_preread on;
        proxy_protocol off;
    }
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    server_tokens off;
    
    # Health check endpoint
    server {
        listen 9000;
        server_name localhost;
        
        location /health {
            proxy_pass http://127.0.0.1:9001/health;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
        }
        
        location /metrics {
            proxy_pass http://127.0.0.1:9001/metrics;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
        }
    }
    
    server {
        listen 80;
        server_name _;
        
        location /.well-known/acme-challenge/ {
            root /var/www/html;
        }
        
        location / {
            return 301 https://\$server_name\$request_uri;
        }
    }
}
EOF
}

# Generate client configurations
generate_client_configs() {
    log_info "Generating client configurations..."
    
    mkdir -p /root/stealthflow-configs
    
    # REALITY configuration
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
    }
  ]
}
EOF

    # Subscription URLs
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
}

# Show final information
show_config_info() {
    echo
    log_info "=== Configuration Generated Successfully ==="
    echo "UUID: $UUID"
    echo "REALITY Private Key: $REALITY_PRIVATE_KEY"
    echo "REALITY Public Key: $REALITY_PUBLIC_KEY"
    echo "REALITY Short ID: $REALITY_SHORT_ID"
    echo "Trojan Password: $TROJAN_PASSWORD"
    echo
    echo "Configuration files saved to:"
    echo "  - Xray: /etc/xray/config.json"
    echo "  - Nginx: /etc/nginx/nginx.conf" 
    echo "  - Client configs: /root/stealthflow-configs/"
    echo "=============================================="
}

# Main function
main() {
    # Check environment variables
    if [[ -z "$DOMAIN" ]]; then
        log_error "DOMAIN environment variable is required"
        exit 1
    fi
    
    # Generate keys and passwords
    if [[ -z "$UUID" ]]; then
        generate_uuid
    fi
    
    if [[ -z "$REALITY_PRIVATE_KEY" ]]; then
        generate_reality_keys
    fi
    
    if [[ -z "$TROJAN_PASSWORD" ]]; then
        generate_trojan_password
    fi
    
    # Generate configurations
    generate_xray_config
    generate_nginx_config
    generate_client_configs
    
    # Show information
    show_config_info
}

# Main execution
main "$@"
