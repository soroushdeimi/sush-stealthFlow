#!/bin/bash
set -e

# StealthFlow Docker Entrypoint Script
# Docker entry point script for StealthFlow server

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[ENTRYPOINT]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[ENTRYPOINT]${NC} $1"
}

log_error() {
    echo -e "${RED}[ENTRYPOINT]${NC} $1"
}

# Generate REALITY keys if not provided
generate_reality_keys() {
    if [[ -z "$REALITY_PRIVATE_KEY" ]]; then
        log_info "Generating REALITY keys..."
        REALITY_KEYS=$(/usr/local/bin/xray x25519)
        export REALITY_PRIVATE_KEY=$(echo "$REALITY_KEYS" | grep "Private key:" | cut -d' ' -f3)
        export REALITY_PUBLIC_KEY=$(echo "$REALITY_KEYS" | grep "Public key:" | cut -d' ' -f3)
        log_info "Generated REALITY keys"
    fi
    
    if [[ -z "$REALITY_SHORT_ID" ]]; then
        export REALITY_SHORT_ID=$(openssl rand -hex 8)
        log_info "Generated REALITY Short ID: $REALITY_SHORT_ID"
    fi
}

# Generate UUID if not present
generate_uuid() {
    if [[ -z "$UUID" ]]; then
        if command -v uuidgen &> /dev/null; then
            export UUID=$(uuidgen)
        else
            export UUID=$(cat /proc/sys/kernel/random/uuid)
        fi
        log_info "Generated UUID: $UUID"
    fi
}

# Generate Trojan password if not present
generate_trojan_password() {
    if [[ -z "$TROJAN_PASSWORD" ]]; then
        export TROJAN_PASSWORD=$(openssl rand -base64 32)
        log_info "Generated Trojan password"
    fi
}

# Configure configuration files
configure_files() {
    log_info "Configuring Xray..."
    
    # Replace variables in Xray config
    envsubst < /etc/xray/config.json.template > /etc/xray/config.json
    
    # Set permissions
    chown xray:xray /etc/xray/config.json
    chmod 600 /etc/xray/config.json
    
    log_info "Configuring Nginx..."
    
    # Replace variables in Nginx config
    envsubst < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf
    
    # Test Nginx config
    nginx -t
}

# Setup automatic SSL certificates
setup_ssl() {
    if [[ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]] && [[ "$SSL_ENABLED" == "true" ]]; then
        log_info "Setting up SSL certificate..."
        
        # Stop nginx temporarily
        supervisorctl stop nginx || true
        
        # Request certificate
        certbot certonly --standalone \
            --email "${EMAIL}" \
            --agree-tos \
            --no-eff-email \
            --domains "${DOMAIN},cdn1.${DOMAIN},cdn2.${DOMAIN},cdn3.${DOMAIN}" \
            --non-interactive || log_warn "SSL certificate generation failed"
        
        # Restart nginx
        supervisorctl start nginx || true
    fi
}

# Create health check file
create_health_endpoint() {
    cat > /var/www/html/health << 'EOF'
{
  "status": "healthy",
  "service": "stealthflow-server",
  "timestamp": "$(date -Iseconds)",
  "version": "1.0.0"
}
EOF
    
    # Create endpoint for health check
    cat > /var/www/html/health.php << 'EOF'
<?php
header('Content-Type: application/json');
echo json_encode([
    'status' => 'healthy',
    'service' => 'stealthflow-server',
    'timestamp' => date('c'),
    'version' => '1.0.0',
    'xray' => file_exists('/var/run/xray.pid'),
    'nginx' => file_exists('/var/run/nginx.pid')
]);
?>
EOF
}

# Show configuration information
show_config_info() {
    echo
    log_info "=== StealthFlow Server Configuration ==="
    echo "Domain: ${DOMAIN:-Not Set}"
    echo "UUID: ${UUID:-Not Set}"
    echo "REALITY Public Key: ${REALITY_PUBLIC_KEY:-Not Set}"
    echo "REALITY Short ID: ${REALITY_SHORT_ID:-Not Set}"
    echo "SSL Enabled: ${SSL_ENABLED:-false}"
    echo "Email: ${EMAIL:-Not Set}"
    echo "=================================="
    echo
}

# Main function
main() {
    log_info "Starting StealthFlow Server..."
    
    # Check required environment variables
    if [[ -z "$DOMAIN" ]]; then
        log_error "DOMAIN environment variable is required"
        exit 1
    fi
    
    # Generate keys and required variables
    generate_uuid
    generate_reality_keys
    generate_trojan_password
    
    # Configure files
    configure_files
    
    # Setup SSL
    setup_ssl
    
    # Create health endpoint
    create_health_endpoint
    
    # Show information
    show_config_info
    
    log_info "Configuration complete, starting services..."
    
    # Execute main command
    exec "$@"
}

# Main execution
main "$@"
