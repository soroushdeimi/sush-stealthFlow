#!/bin/bash

# StealthFlow Quick Setup Script
# Quick setup script for StealthFlow

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration variables
SETUP_TYPE=""
DOMAIN=""
EMAIL=""
INSTALL_DIR=""
AUTO_START=true
ENABLE_MONITORING=false
ENABLE_P2P=true

# GitHub repository configuration - CHANGE THIS to your actual repository
GITHUB_REPO="soroushdeimi/sush-stealthFlow"
GITHUB_RAW_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/main"

# Helper functions
log_info() {
    echo -e "${GREEN}[SETUP]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Show logo
show_logo() {
    echo -e "${PURPLE}"
    cat << 'EOF'
███████╗████████╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗███████╗██╗      ██████╗ ██╗    ██╗
██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║██╔════╝██║     ██╔═══██╗██║    ██║
███████╗   ██║   █████╗  ███████║██║     ██║   ███████║█████╗  ██║     ██║   ██║██║ █╗ ██║
╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██║   ██╔══██║██╔══╝  ██║     ██║   ██║██║███╗██║
███████║   ██║   ███████╗██║  ██║███████╗██║   ██║  ██║██║     ███████╗╚██████╔╝╚███╔███╔╝
╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝ 
EOF
    echo -e "${NC}"
    echo -e "${BLUE}=== Multi-Layer Anti-Censorship System ===${NC}"
    echo -e "${YELLOW}REALITY • Trojan • Multi-CDN • P2P Fallback${NC}"
    echo
}

# Show usage guide
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -t, --type TYPE         Setup type (server|client|docker|k8s)"
    echo "  -d, --domain DOMAIN     Domain name (required for server)"
    echo "  -e, --email EMAIL       Email for SSL certificates"
    echo "  -i, --install-dir DIR   Installation directory"
    echo "  --no-autostart          Don't start services automatically"
    echo "  --enable-monitoring     Enable Prometheus/Grafana monitoring"
    echo "  --disable-p2p           Disable P2P fallback"
    echo "  -h, --help              Show this help message"
    echo
    echo "Examples:"
    echo "  $0 -t server -d proxy.example.com -e admin@example.com"
    echo "  $0 -t client"
    echo "  $0 -t docker -d proxy.example.com --enable-monitoring"
}

# Parse arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                SETUP_TYPE="$2"
                shift 2
                ;;
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
            --no-autostart)
                AUTO_START=false
                shift
                ;;
            --enable-monitoring)
                ENABLE_MONITORING=true
                shift
                ;;
            --disable-p2p)
                ENABLE_P2P=false
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
    log_step "Checking prerequisites..."
    
    # Check operating system
    if [[ "$OSTYPE" =~ ^darwin ]]; then
        OS="macos"
        PACKAGE_MANAGER="brew"
    elif [[ "$OSTYPE" =~ ^linux ]]; then
        OS="linux"
        if command -v apt-get &> /dev/null; then
            PACKAGE_MANAGER="apt"
        elif command -v yum &> /dev/null; then
            PACKAGE_MANAGER="yum"
        elif command -v pacman &> /dev/null; then
            PACKAGE_MANAGER="pacman"
        else
            log_error "Unsupported package manager"
            exit 1
        fi
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    log_info "Detected OS: $OS with package manager: $PACKAGE_MANAGER"
    
    # Check root access if needed
    if [[ "$SETUP_TYPE" == "server" && $EUID -ne 0 ]]; then
        log_error "Server setup requires root privileges. Please run with sudo."
        exit 1
    fi
}

# Install base dependencies
install_dependencies() {
    log_step "Installing dependencies..."
    
    case $PACKAGE_MANAGER in
        apt)
            apt update
            apt install -y curl wget unzip git python3 python3-pip
            ;;
        yum)
            yum update -y
            yum install -y curl wget unzip git python3 python3-pip
            ;;
        pacman)
            pacman -Syu --noconfirm
            pacman -S --noconfirm curl wget unzip git python python-pip
            ;;
        brew)
            brew update
            brew install curl wget python3 git
            ;;
    esac
    
    # Install Docker if needed
    if [[ "$SETUP_TYPE" == "docker" || "$SETUP_TYPE" == "k8s" ]]; then
        if ! command -v docker &> /dev/null; then
            log_info "Installing Docker..."
            curl -fsSL https://get.docker.com | sh
            
            if [[ "$OS" == "linux" ]]; then
                systemctl enable docker
                systemctl start docker
                usermod -aG docker $USER || true
            fi
        fi
        
        if [[ "$SETUP_TYPE" == "docker" ]] && ! command -v docker-compose &> /dev/null; then
            log_info "Installing Docker Compose..."
            pip3 install docker-compose
        fi
    fi
    
    # Install kubectl for Kubernetes
    if [[ "$SETUP_TYPE" == "k8s" ]] && ! command -v kubectl &> /dev/null; then
        log_info "Installing kubectl..."
        curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
        chmod +x kubectl
        mv kubectl /usr/local/bin/
    fi
}

# Setup server
setup_server() {
    log_step "Setting up StealthFlow server..."
    
    if [[ -z "$DOMAIN" ]]; then
        log_error "Domain is required for server setup"
        exit 1
    fi
    
    if [[ -z "$EMAIL" ]]; then
        log_error "Email is required for SSL certificates"
        exit 1
    fi
    
    # Download and run server installation script
    log_info "Downloading server installation script..."
    curl -sSL -o /tmp/stealthflow-install.sh "${GITHUB_RAW_URL}/server/scripts/install.sh"
    chmod +x /tmp/stealthflow-install.sh
    
    # Run script with specified parameters
    DOMAIN="$DOMAIN" EMAIL="$EMAIL" /tmp/stealthflow-install.sh
    
    log_info "Server setup completed!"
    log_info "Server is running on: https://$DOMAIN"
}

# Setup client
setup_client() {
    log_step "Setting up StealthFlow client..."
    
    # Determine installation directory
    if [[ -z "$INSTALL_DIR" ]]; then
        INSTALL_DIR="$HOME/.stealthflow"
    fi
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Download client files
    log_info "Downloading client files..."
    curl -sSL -o stealthflow_client.py "${GITHUB_RAW_URL}/client/core/stealthflow_client.py"
    curl -sSL -o profile_manager.py "${GITHUB_RAW_URL}/client/profiles/profile_manager.py"
    curl -sSL -o stealthflow_gui.py "${GITHUB_RAW_URL}/client/ui/stealthflow_gui.py"
    curl -sSL -o requirements.txt "${GITHUB_RAW_URL}/requirements.txt"
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    pip3 install -r requirements.txt
    
    # Create launch script
    cat > stealthflow << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python3 stealthflow_client.py "$@"
EOF
    chmod +x stealthflow
    
    # Create symbolic link
    ln -sf "$INSTALL_DIR/stealthflow" /usr/local/bin/stealthflow 2>/dev/null || true
    
    log_info "Client setup completed!"
    log_info "Installation directory: $INSTALL_DIR"
    log_info "Run 'stealthflow --help' to get started"
}

# Docker setup
setup_docker() {
    log_step "Setting up StealthFlow with Docker..."
    
    if [[ -z "$DOMAIN" ]]; then
        read -p "Enter your domain: " DOMAIN
    fi
    
    if [[ -z "$EMAIL" ]]; then
        read -p "Enter your email: " EMAIL
    fi
    
    # Download Docker files
    log_info "Downloading Docker configuration..."
    curl -sSL -o docker-compose.yml "${GITHUB_RAW_URL}/docker-compose.yml"
    curl -sSL -o .env.example "${GITHUB_RAW_URL}/.env.example"
    
    # Setup environment variables
    cp .env.example .env
    sed -i "s/DOMAIN=.*/DOMAIN=$DOMAIN/" .env
    sed -i "s/EMAIL=.*/EMAIL=$EMAIL/" .env
    sed -i "s/UUID=.*/UUID=$(uuidgen)/" .env
    sed -i "s/TROJAN_PASSWORD=.*/TROJAN_PASSWORD=$(openssl rand -base64 32)/" .env
    
    # Start Docker Compose
    if [[ "$ENABLE_MONITORING" == "true" ]]; then
        docker-compose --profile monitoring up -d
    else
        docker-compose up -d
    fi
    
    log_info "Docker setup completed!"
    log_info "Services are starting up..."
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check status
    docker-compose ps
}

# Kubernetes setup
setup_k8s() {
    log_step "Setting up StealthFlow on Kubernetes..."
    
    if [[ -z "$DOMAIN" ]]; then
        read -p "Enter your domain: " DOMAIN
    fi
    
    if [[ -z "$EMAIL" ]]; then
        read -p "Enter your email: " EMAIL
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Download Helm chart
    log_info "Downloading Helm chart..."
    curl -sSL -o stealthflow-chart.tgz "https://github.com/${GITHUB_REPO}/releases/latest/download/stealthflow-helm-chart.tgz"
    tar -xzf stealthflow-chart.tgz
    
    # Install with Helm
    if command -v helm &> /dev/null; then
        helm upgrade --install stealthflow ./stealthflow \
            --namespace stealthflow \
            --create-namespace \
            --set config.domain="$DOMAIN" \
            --set config.email="$EMAIL" \
            --set monitoring.enabled="$ENABLE_MONITORING"
    else
        # Use kubectl
        log_info "Installing with kubectl..."
        curl -sSL "${GITHUB_RAW_URL}/k8s/stealthflow.yaml" | \
        sed "s/example.com/$DOMAIN/g" | \
        kubectl apply -f -
    fi
    
    log_info "Kubernetes setup completed!"
    log_info "Check status with: kubectl get pods -n stealthflow"
}

# Show final information
show_final_info() {
    echo
    log_info "=== StealthFlow Setup Complete! ==="
    echo
    
    case $SETUP_TYPE in
        server)
            echo -e "${GREEN}Server Information:${NC}"
            echo "  Domain: https://$DOMAIN"
            echo "  Health Check: https://$DOMAIN:9000/health"
            echo "  Configuration files: /root/stealthflow-configs/"
            if [[ "$ENABLE_MONITORING" == "true" ]]; then
                echo "  Grafana: https://$DOMAIN:3000"
                echo "  Prometheus: https://$DOMAIN:9090"
            fi
            ;;
        client)
            echo -e "${GREEN}Client Information:${NC}"
            echo "  Installation: $INSTALL_DIR"
            echo "  Command: stealthflow --help"
            echo "  GUI: python3 $INSTALL_DIR/stealthflow_gui.py"
            ;;
        docker)
            echo -e "${GREEN}Docker Information:${NC}"
            echo "  Status: docker-compose ps"
            echo "  Logs: docker-compose logs -f"
            echo "  Stop: docker-compose down"
            echo "  Server: https://$DOMAIN"
            ;;
        k8s)
            echo -e "${GREEN}Kubernetes Information:${NC}"
            echo "  Namespace: stealthflow"
            echo "  Status: kubectl get pods -n stealthflow"
            echo "  Logs: kubectl logs -l app=stealthflow-server -n stealthflow"
            echo "  Service: kubectl get svc -n stealthflow"
            ;;
    esac
    
    echo
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Verify the installation is working"
    echo "2. Configure your clients"
    echo "3. Test the connection"
    echo "4. Set up monitoring and backups"
    echo
    echo -e "${CYAN}Documentation: https://github.com/${GITHUB_REPO}${NC}"
    echo -e "${CYAN}Support: https://github.com/${GITHUB_REPO}/issues${NC}"
    echo
}

# Main function
main() {
    show_logo
    
    parse_arguments "$@"
    
    if [[ -z "$SETUP_TYPE" ]]; then
        echo -e "${YELLOW}Please select setup type:${NC}"
        echo "1) Server (Install on VPS/Server)"
        echo "2) Client (Install on local machine)"
        echo "3) Docker (Run with Docker)"
        echo "4) Kubernetes (Deploy to K8s cluster)"
        echo
        read -p "Enter choice [1-4]: " choice
        
        case $choice in
            1) SETUP_TYPE="server" ;;
            2) SETUP_TYPE="client" ;;
            3) SETUP_TYPE="docker" ;;
            4) SETUP_TYPE="k8s" ;;
            *) log_error "Invalid choice"; exit 1 ;;
        esac
    fi
    
    check_prerequisites
    install_dependencies
    
    case $SETUP_TYPE in
        server)
            setup_server
            ;;
        client)
            setup_client
            ;;
        docker)
            setup_docker
            ;;
        k8s)
            setup_k8s
            ;;
        *)
            log_error "Invalid setup type: $SETUP_TYPE"
            exit 1
            ;;
    esac
    
    show_final_info
}

# Main execution
main "$@"
