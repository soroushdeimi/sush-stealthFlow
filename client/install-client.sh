#!/bin/bash

# StealthFlow Client Installation Script
# Automatic installation of StealthFlow client

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logo
echo -e "${BLUE}
███████╗████████╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗███████╗██╗      ██████╗ ██╗    ██╗
██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║██╔════╝██║     ██╔═══██╗██║    ██║
███████╗   ██║   █████╗  ███████║██║     ██║   ███████║█████╗  ██║     ██║   ██║██║ █╗ ██║
╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██║   ██╔══██║██╔══╝  ██║     ██║   ██║██║███╗██║
███████║   ██║   ███████╗██║  ██║███████╗██║   ██║  ██║██║     ███████╗╚██████╔╝╚███╔███╔╝
╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝ 
${NC}"

echo -e "${GREEN}=== StealthFlow Client Installer ===${NC}"
echo

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

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/debian_version ]; then
            OS="debian"
        elif [ -f /etc/redhat-release ]; then
            OS="redhat"
        else
            OS="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        log_error "Unsupported operating system"
        exit 1
    fi
    
    log_info "Detected OS: $OS"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    
    case $OS in
        "debian")
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv curl wget unzip
            ;;
        "redhat")
            sudo yum update -y
            sudo yum install -y python3 python3-pip curl wget unzip
            ;;
        "macos")
            # Check for Homebrew installation
            if ! command -v brew &> /dev/null; then
                log_info "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install python3
            ;;
    esac
}

# Install Xray
install_xray() {
    log_info "Installing Xray-core..."
    
    # Detect architecture
    ARCH=$(uname -m)
    case $ARCH in
        x86_64) XRAY_ARCH="64" ;;
        aarch64|arm64) XRAY_ARCH="arm64-v8a" ;;
        armv7l) XRAY_ARCH="arm32-v7a" ;;
        *) log_error "Unsupported architecture: $ARCH"; exit 1 ;;
    esac
    
    # Download latest version
    XRAY_VERSION=$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases/latest | grep -o '"tag_name": *"[^"]*"' | cut -d'"' -f4)
    
    if [[ -z "$XRAY_VERSION" ]]; then
        log_error "Error getting Xray version"
        exit 1
    fi
    
    log_info "Downloading Xray $XRAY_VERSION..."
    
    cd /tmp
    
    if [[ "$OS" == "macos" ]]; then
        wget "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/Xray-macos-${XRAY_ARCH}.zip"
        unzip -o "Xray-macos-${XRAY_ARCH}.zip"
    else
        wget "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/Xray-linux-${XRAY_ARCH}.zip"
        unzip -o "Xray-linux-${XRAY_ARCH}.zip"
    fi
    
    # Install in appropriate path
    INSTALL_PATH="/usr/local/bin"
    
    sudo mkdir -p "$INSTALL_PATH"
    sudo mv xray "$INSTALL_PATH/"
    sudo chmod +x "$INSTALL_PATH/xray"
    
    log_info "Xray installed at $INSTALL_PATH/xray"
}

# Setup Python environment
setup_python_env() {
    log_info "Setting up Python environment..."
    
    # Determine installation path
    INSTALL_DIR="$HOME/StealthFlow"
    
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install required libraries
    cat > requirements.txt << EOF
asyncio
aiohttp
websockets
aiortc
pyyaml
tkinter
requests
psutil
EOF
    
    pip install -r requirements.txt
    
    log_info "Python environment ready at $INSTALL_DIR"
}

# Download StealthFlow files
download_stealthflow() {
    log_info "Downloading StealthFlow files..."
    
    # Here should download from actual repository
    # For now, create local structure
    
    log_warn "Files should be copied manually for now"
    
    # Create directory structure
    mkdir -p client/core client/ui client/profiles p2p/webrtc p2p/signaling utils
    
    # Create sample profile file
    cat > client/profiles/default.yaml << EOF
profiles:
  - name: "REALITY-Direct"
    protocol: "vless"
    server: "YOUR_SERVER_IP"
    port: 443
    uuid: "YOUR_UUID"
    security: "reality"
    reality_settings:
      serverName: "www.microsoft.com"
      fingerprint: "chrome"
      show: false
      publicKey: "YOUR_REALITY_PUBLIC_KEY"
      shortId: "YOUR_SHORT_ID"
      spiderX: "/"
    priority: 1
    enabled: true
  
  - name: "Trojan-CDN1"
    protocol: "trojan"
    server: "cdn1.yourdomain.com"
    port: 443
    password: "YOUR_TROJAN_PASSWORD"
    security: "tls"
    priority: 2
    enabled: true
EOF
}

# Create launcher scripts
create_launchers() {
    log_info "Creating launcher scripts..."
    
    # GUI script
    cat > stealthflow-gui.sh << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source venv/bin/activate
python3 client/ui/stealthflow_gui.py
EOF
    
    # CLI script
    cat > stealthflow-cli.sh << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source venv/bin/activate
python3 client/core/stealthflow_client.py
EOF
    
    # P2P Helper script
    cat > stealthflow-p2p-helper.sh << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
source venv/bin/activate
python3 p2p/webrtc/p2p_fallback.py helper
EOF
    
    chmod +x *.sh
    
    # Create symlinks on macOS/Linux
    if [[ "$OS" != "windows" ]]; then
        sudo ln -sf "$PWD/stealthflow-gui.sh" /usr/local/bin/stealthflow-gui
        sudo ln -sf "$PWD/stealthflow-cli.sh" /usr/local/bin/stealthflow-cli
        sudo ln -sf "$PWD/stealthflow-p2p-helper.sh" /usr/local/bin/stealthflow-p2p-helper
    fi
}

# Create desktop entry on Linux
create_desktop_entry() {
    if [[ "$OS" == "debian" ]] || [[ "$OS" == "redhat" ]]; then
        log_info "Creating desktop entry..."
        
        mkdir -p ~/.local/share/applications
        
        cat > ~/.local/share/applications/stealthflow.desktop << EOF
[Desktop Entry]
Name=StealthFlow
Comment=Smart Anti-Censorship Client
Exec=$PWD/stealthflow-gui.sh
Icon=$PWD/icon.png
Terminal=false
Type=Application
Categories=Network;Security;
EOF
        
        chmod +x ~/.local/share/applications/stealthflow.desktop
    fi
}

# Test installation
test_installation() {
    log_info "Testing installation..."
    
    # Check Xray
    if command -v xray &> /dev/null; then
        XRAY_VERSION=$(xray version | head -n 1)
        log_info "Xray installed: $XRAY_VERSION"
    else
        log_error "Xray not installed"
        return 1
    fi
    
    # Check Python modules
    source venv/bin/activate
    if python3 -c "import asyncio, aiohttp, websockets" &> /dev/null; then
        log_info "Python modules available"
    else
        log_error "Error with Python modules"
        return 1
    fi
    
    log_info "Installation completed successfully!"
    return 0
}

# Show final information
show_final_info() {
    echo
    echo -e "${GREEN}=== Installation Complete! ===${NC}"
    echo
    echo -e "${YELLOW}How to run:${NC}"
    
    if [[ "$OS" == "macos" ]] || [[ "$OS" == "debian" ]] || [[ "$OS" == "redhat" ]]; then
        echo "GUI: stealthflow-gui"
        echo "CLI: stealthflow-cli"
        echo "P2P Helper: stealthflow-p2p-helper"
        echo
        echo "Or from installation directory:"
        echo "./stealthflow-gui.sh"
        echo "./stealthflow-cli.sh"
    fi
    
    echo
    echo -e "${YELLOW}Configuration:${NC}"
    echo "1. Edit profile file: client/profiles/default.yaml"
    echo "2. Enter your server information"
    echo "3. Run the application"
    echo
    echo -e "${BLUE}Installation path: $PWD${NC}"
    echo
    echo -e "${GREEN}StealthFlow is ready to use!${NC}"
}

# Main function
main() {
    # Check permissions
    if [[ $EUID -eq 0 ]] && [[ "$OS" != "macos" ]]; then
        log_error "Do not run this script as root"
        exit 1
    fi
    
    detect_os
    
    # Install dependencies (may need sudo)
    if [[ "$OS" != "macos" ]]; then
        sudo -v  # Request sudo access
    fi
    
    install_dependencies
    install_xray
    setup_python_env
    download_stealthflow
    create_launchers
    
    if [[ "$OS" == "debian" ]] || [[ "$OS" == "redhat" ]]; then
        create_desktop_entry
    fi
    
    if test_installation; then
        show_final_info
    else
        log_error "Installation error. Please try again."
        exit 1
    fi
}

# Run
main "$@"
