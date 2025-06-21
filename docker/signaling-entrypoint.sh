#!/bin/bash
set -e

# StealthFlow P2P Signaling Server Docker Entrypoint
# Docker entry point script for P2P signaling server

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[SIGNALING]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[SIGNALING]${NC} $1"
}

log_error() {
    echo -e "${RED}[SIGNALING]${NC} $1"
}

log_debug() {
    if [ "$DEBUG" = "true" ]; then
        echo -e "${BLUE}[SIGNALING DEBUG]${NC} $1"
    fi
}

# Check system dependencies
check_dependencies() {
    log_info "Checking system dependencies..."
    
    # Check if Python is available
    if ! command -v python3 > /dev/null 2>&1; then
        log_error "Python 3 is not installed"
        exit 1
    fi
        exit 1
    fi
    
    log_info "Node.js version: $(node --version)"
    log_info "NPM version: $(npm --version)"
}

# Setup environment variables
setup_environment() {
    export SIGNALING_PORT=${SIGNALING_PORT:-8765}
    export LOG_LEVEL=${LOG_LEVEL:-INFO}
    export ALLOWED_ORIGINS=${ALLOWED_ORIGINS:-*}
    export NODE_ENV=${NODE_ENV:-production}
    
    log_info "Environment configured:"
    log_info "  Port: $SIGNALING_PORT"
    log_info "  Log Level: $LOG_LEVEL"
    log_info "  Allowed Origins: $ALLOWED_ORIGINS"
    log_info "  Node Environment: $NODE_ENV"
}

# Create required directories
create_directories() {
    mkdir -p /var/log/signaling
    
    # Set permissions
    chown -R $(whoami) /var/log/signaling 2>/dev/null || true
}

# Health check
health_check() {
    log_info "Setting up health monitoring..."
    
    # Create health check file
    cat > /tmp/health-check.js << 'EOF'
const WebSocket = require('ws');

function healthCheck() {
    return new Promise((resolve, reject) => {
        const ws = new WebSocket(`ws://localhost:${process.env.SIGNALING_PORT || 8765}`);
        
        const timeout = setTimeout(() => {
            ws.terminate();
            reject(new Error('Health check timeout'));
        }, 5000);
        
        ws.on('open', () => {
            clearTimeout(timeout);
            ws.close();
            resolve(true);
        });
        
        ws.on('error', (error) => {
            clearTimeout(timeout);
            reject(error);
        });
    });
}

if (require.main === module) {
    healthCheck()
        .then(() => {
            console.log('Health check passed');
            process.exit(0);
        })
        .catch((error) => {
            console.error('Health check failed:', error.message);
            process.exit(1);
        });
}

module.exports = healthCheck;
EOF
}

# Show startup information
show_startup_info() {
    echo
    log_info "=== StealthFlow P2P Signaling Server ==="
    log_info "Starting on port: $SIGNALING_PORT"
    log_info "Log level: $LOG_LEVEL"
    log_info "Process ID: $$"
    log_info "User: $(whoami)"
    log_info "Working directory: $(pwd)"
    echo "========================================"
    echo
}

# Signal handlers
setup_signal_handlers() {
    # Handle shutdown signals
    trap 'log_info "Received SIGTERM, shutting down gracefully..."; exit 0' TERM
    trap 'log_info "Received SIGINT, shutting down gracefully..."; exit 0' INT
}

# Main function
main() {
    log_info "Initializing StealthFlow P2P Signaling Server..."
    
    # Check dependencies
    check_dependencies
    
    # Setup environment
    setup_environment
    
    # Create directories
    create_directories
    
    # Setup health check
    health_check
    
    # Setup signal handlers
    setup_signal_handlers
    
    # Show startup information
    show_startup_info
    
    log_info "Starting signaling server..."
    
    # Execute main command
    exec "$@"
}

# Main execution
main "$@"
