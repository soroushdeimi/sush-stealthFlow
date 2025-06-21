#!/bin/bash
#
# StealthFlow Project Launcher for Linux
# Smart Anti-Censorship Tool Launcher
#
# This script allows you to easily run different StealthFlow components:
# - GUI Client
# - CLI Client  
# - P2P Signaling Server
# - Management Tools
#

set -euo pipefail

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check for required dependencies
check_requirements() {
    log_info "Checking requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        return 1
    fi
    
    # Check Python modules
    if ! python3 -c "import yaml, aiohttp, asyncio" 2>/dev/null; then
        log_error "Required Python dependencies not installed"
        log_info "To install dependencies run:"
        log_info "pip3 install -r requirements.txt"
        return 1
    fi
    
    # Check Xray (optional)
    if ! command -v xray &> /dev/null; then
        log_warn "Xray not installed or not in PATH"
        log_warn "Some features may not work without Xray"
    fi
    
    return 0
}

# Run GUI client
run_client_gui() {
    log_info "Starting StealthFlow GUI client..."
    
    local gui_path="$PROJECT_ROOT/client/ui/stealthflow_gui.py"
    if [[ ! -f "$gui_path" ]]; then
        log_error "GUI file not found: $gui_path"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
    python3 "$gui_path"
}

# Run CLI client
run_client_cli() {
    log_info "Starting StealthFlow CLI client..."
    
    local cli_path="$PROJECT_ROOT/client/core/stealthflow_client.py"
    if [[ ! -f "$cli_path" ]]; then
        log_error "CLI file not found: $cli_path"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
    python3 "$cli_path"
}

# Run P2P signaling server
run_p2p_signaling() {
    log_info "Starting P2P signaling server..."
    
    local signaling_path="$PROJECT_ROOT/p2p/signaling/signaling_server.py"
    if [[ ! -f "$signaling_path" ]]; then
        log_error "Signaling file not found: $signaling_path"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
    python3 "$signaling_path"
}

# Run P2P helper
run_p2p_helper() {
    log_info "Starting P2P Helper..."
    
    local p2p_path="$PROJECT_ROOT/p2p/webrtc/p2p_fallback.py"
    if [[ ! -f "$p2p_path" ]]; then
        log_error "P2P file not found: $p2p_path"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
    python3 "$p2p_path" helper
}

# Generate configuration
generate_config() {
    log_info "Starting config generation..."
    
    local generator_path="$PROJECT_ROOT/utils/config_generator.py"
    if [[ ! -f "$generator_path" ]]; then
        log_error "Config generator not found: $generator_path"
        return 1
    fi
    
    # Get information from user
    read -p "Config type (reality/trojan/ss): " config_type
    config_type=$(echo "$config_type" | tr '[:upper:]' '[:lower:]')
    
    if [[ ! "$config_type" =~ ^(reality|trojan|ss)$ ]]; then
        log_error "Invalid config type"
        return 1
    fi
    
    read -p "Server address: " server
    if [[ -z "$server" ]]; then
        log_error "Server address is required"
        return 1
    fi
    
    read -p "Port (default 443): " port
    port=${port:-443}
    
    cd "$PROJECT_ROOT"
    
    case "$config_type" in
        reality)
            read -p "UUID: " uuid
            read -p "Public Key: " public_key
            read -p "Short ID: " short_id
            
            python3 "$generator_path" \
                --type reality \
                --server "$server" \
                --port "$port" \
                --uuid "$uuid" \
                --public-key "$public_key" \
                --short-id "$short_id" \
                --share-url
            ;;
        trojan|ss)
            read -p "Password: " password
            
            python3 "$generator_path" \
                --type "$config_type" \
                --server "$server" \
                --port "$port" \
                --password "$password" \
                --share-url
            ;;
    esac
}

# Run tests
run_tests() {
    log_info "Running StealthFlow tests..."
    
    local test_path="$PROJECT_ROOT/tests/test_stealthflow.py"
    if [[ ! -f "$test_path" ]]; then
        log_error "Test file not found: $test_path"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
    python3 "$test_path"
}

# Show system status
show_status() {
    echo "StealthFlow System Status"
    echo "=========================================="
    
    # Check Python
    local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "Python: $python_version"
    
    # Check Xray
    if command -v xray &> /dev/null; then
        local xray_version=$(xray version 2>/dev/null | head -n1 || echo "Unknown version")
        echo "Xray: $xray_version"
    else
        echo "Xray: Not installed"
    fi
    
    # Check config files
    if [[ -f "$PROJECT_ROOT/stealthflow_profiles.yaml" ]]; then
        echo "Profiles file: Available"
    else
        echo "Profiles file: Not found"
    fi
    
    if [[ -f "$PROJECT_ROOT/stealthflow_settings.json" ]]; then
        echo "Settings file: Available"
    else
        echo "Settings file: Not found"
    fi
    
    # Check Python dependencies
    if python3 -c "import yaml, aiohttp, websockets" 2>/dev/null; then
        echo "Python dependencies: Installed"
    else
        echo "Python dependencies: Not installed"
    fi
}

# Initial project setup
setup_project() {
    log_info "Setting up project..."
    
    # Create default config files
    local profiles_file="$PROJECT_ROOT/stealthflow_profiles.yaml"
    if [[ ! -f "$profiles_file" ]]; then
        log_info "Creating sample profiles file..."
        
        cat > "$profiles_file" << 'EOF'
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
        log_info "Profiles file created: $profiles_file"
    fi
    
    # Create settings file
    local settings_file="$PROJECT_ROOT/stealthflow_settings.json"
    if [[ ! -f "$settings_file" ]]; then
        log_info "Creating sample settings file..."
        
        cat > "$settings_file" << 'EOF'
{
  "socks_port": 10808,
  "http_port": 10809,
  "test_interval": 30,
  "max_latency": 5000,
  "retry_count": 3,
  "use_doh": true,
  "dns_servers": [
    "https://dns.google/dns-query",
    "https://cloudflare-dns.com/dns-query"
  ],
  "auto_switch": true,
  "log_level": "INFO",
  "p2p_signaling_server": "wss://signaling.stealthflow.org"
}
EOF
        log_info "Settings file created: $settings_file"
    fi
    
    log_info "Setup completed!"
    echo ""
    echo "Next steps:"
    echo "1. Edit stealthflow_profiles.yaml file"
    echo "2. Enter your server information"
    echo "3. Start with './stealthflow.sh gui'"
}

# Show help
show_help() {
    cat << EOF

███████╗████████╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗███████╗██╗      ██████╗ ██╗    ██╗
██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║██╔════╝██║     ██╔═══██╗██║    ██║
███████╗   ██║   █████╗  ███████║██║     ██║   ███████║█████╗  ██║     ██║   ██║██║ █╗ ██║
╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██║   ██╔══██║██╔══╝  ██║     ██║   ██║██║███╗██║
███████║   ██║   ███████╗██║  ██║███████╗██║   ██║  ██║██║     ███████╗╚██████╔╝╚███╔███╔╝
╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝ 

StealthFlow - Smart Anti-Censorship System
============================================================

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  gui              Run GUI interface
  cli              Run command line interface
  p2p-signaling    Run P2P signaling server
  p2p-helper       Run P2P helper node
  config           Generate new configuration
  test             Run system tests
  status           Show system status
  setup            Initial project setup
  help             Show this help message

Options:
  --skip-requirements    Skip dependency check

Examples:
  $0 gui                 # Run GUI interface
  $0 cli                 # Run command line
  $0 p2p-signaling       # Run signaling server
  $0 p2p-helper          # Run P2P helper
  $0 config              # Generate new config
  $0 setup               # Initial setup
  $0 status              # Show status
  $0 test                # Run tests

EOF
}

# Main function
main() {
    local command="${1:-help}"
    local skip_requirements=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-requirements)
                skip_requirements=true
                shift
                ;;
            help|--help|-h)
                show_help
                exit 0
                ;;
            gui|cli|p2p-signaling|p2p-helper|config|test|status|setup)
                command="$1"
                shift
                ;;
            *)
                command="$1"
                shift
                ;;
        esac
    done
    
    # Show logo for main commands
    if [[ "$command" != "help" && "$command" != "status" ]]; then
        echo ""
        echo "StealthFlow - Smart Anti-Censorship System"
        echo "============================================================"
        echo ""
    fi
    
    # Check dependencies (skip for certain commands)
    if [[ "$skip_requirements" == false && "$command" != "status" && "$command" != "setup" && "$command" != "help" ]]; then
        if ! check_requirements; then
            log_error "Please install dependencies first:"
            log_info "pip3 install -r requirements.txt"
            exit 1
        fi
    fi
    
    # Change to project directory
    cd "$PROJECT_ROOT"
    
    # Execute command
    case "$command" in
        gui)
            run_client_gui
            ;;
        cli)
            run_client_cli
            ;;
        p2p-signaling)
            run_p2p_signaling
            ;;
        p2p-helper)
            run_p2p_helper
            ;;
        config)
            generate_config
            ;;
        test)
            run_tests
            ;;
        status)
            show_status
            ;;
        setup)
            setup_project
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Invalid command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Handle signals
trap 'echo -e "\nExiting program"; exit 0' INT TERM

# Run main function
main "$@"
