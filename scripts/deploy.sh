#!/bin/bash
#
# StealthFlow Deployment Script
# Automated deployment script for server setup
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
DOMAIN=""
EMAIL=""
INSTALL_DIR="/opt/stealthflow"
BACKUP_DIR="/opt/stealthflow-backup"

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --domain DOMAIN     Domain name (required)"
    echo "  -e, --email EMAIL       Email for SSL certificates"
    echo "  -i, --install-dir DIR   Installation directory"
    echo "  --backup                Create backup before deployment"
    echo "  -h, --help              Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 -d proxy.example.com -e admin@example.com"
    echo "  $0 -d proxy.example.com --backup"
}

# Parse arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--domain)
                DOMAIN="$2"
                shift 2
                ;;
            -e|--email)
                EMAIL="$2"
                shift 2
                ;;
            -i|--install-dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            --backup)
                CREATE_BACKUP=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check root access
    if [[ $EUID -ne 0 ]]; then
        log_error "This script requires root privileges. Please run with sudo."
        exit 1
    fi
    
    # Check required tools
    local required_tools=("curl" "wget" "docker" "docker-compose")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done
    
    # Check domain
    if [[ -z "$DOMAIN" ]]; then
        read -p "Enter domain name: " DOMAIN
        if [[ -z "$DOMAIN" ]]; then
            log_error "Domain is required"
            exit 1
        fi
    fi
    
    # Check email
    if [[ -z "$EMAIL" ]]; then
        read -p "Enter email for SSL certificates: " EMAIL
        if [[ -z "$EMAIL" ]]; then
            log_error "Email is required"
            exit 1
        fi
    fi
}

# Create backup
create_backup() {
    if [[ "$CREATE_BACKUP" == "true" ]] && [[ -d "$INSTALL_DIR" ]]; then
        log_info "Creating backup..."
        
        local backup_name="backup-$(date +%Y%m%d-%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        tar -czf "$BACKUP_DIR/$backup_name.tar.gz" -C "$(dirname "$INSTALL_DIR")" "$(basename "$INSTALL_DIR")"
        
        log_info "Backup created: $BACKUP_DIR/$backup_name.tar.gz"
    fi
}

# Download latest version
download_stealthflow() {
    log_info "Downloading StealthFlow..."
    
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Download from GitHub
    curl -sSL "https://github.com/yourusername/stealthflow/archive/main.tar.gz" | tar -xz --strip-components=1
    
    log_info "StealthFlow downloaded to $INSTALL_DIR"
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    cd "$INSTALL_DIR"
    
    # Copy environment template
    cp .env.example .env
    
    # Generate secrets
    local uuid=$(uuidgen)
    local trojan_password=$(openssl rand -base64 32)
    
    # Update environment file
    sed -i "s/DOMAIN=.*/DOMAIN=$DOMAIN/" .env
    sed -i "s/EMAIL=.*/EMAIL=$EMAIL/" .env
    sed -i "s/UUID=.*/UUID=$uuid/" .env
    sed -i "s/TROJAN_PASSWORD=.*/TROJAN_PASSWORD=$trojan_password/" .env
    
    log_info "Environment configured"
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    cd "$INSTALL_DIR"
    
    # Build and start services
    docker-compose build --no-cache
    docker-compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 30
    
    # Check health
    if docker-compose ps | grep -q "Up"; then
        log_info "Services deployed successfully"
    else
        log_error "Service deployment failed"
        docker-compose logs
        exit 1
    fi
}

# Configure firewall
configure_firewall() {
    log_info "Configuring firewall..."
    
    # Allow required ports
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8765/tcp
    
    # Enable firewall
    ufw --force enable
    
    log_info "Firewall configured"
}

# Show final information
show_final_info() {
    echo ""
    log_info "=== Deployment Complete ==="
    echo ""
    echo "Server Information:"
    echo "  Domain: https://$DOMAIN"
    echo "  Health Check: https://$DOMAIN:9000/health"
    echo "  Installation: $INSTALL_DIR"
    echo ""
    echo "Management Commands:"
    echo "  Status: cd $INSTALL_DIR && docker-compose ps"
    echo "  Logs: cd $INSTALL_DIR && docker-compose logs -f"
    echo "  Restart: cd $INSTALL_DIR && docker-compose restart"
    echo "  Stop: cd $INSTALL_DIR && docker-compose down"
    echo ""
    echo "Configuration files are located in: $INSTALL_DIR"
    echo ""
}

# Main function
main() {
    echo "StealthFlow Deployment Script"
    echo "============================="
    echo ""
    
    parse_arguments "$@"
    check_prerequisites
    create_backup
    download_stealthflow
    setup_environment
    deploy_services
    configure_firewall
    show_final_info
}

# Run main function
main "$@"
