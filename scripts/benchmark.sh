#!/bin/bash
#
# StealthFlow Benchmark Script
# Performance testing and benchmarking
#

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
TEST_DURATION=60
CONCURRENT_CONNECTIONS=10
TEST_URL="https://www.google.com/generate_204"
PROXY_HOST="127.0.0.1"
PROXY_PORT="10808"

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
    echo "  -d, --duration SECONDS  Test duration (default: 60)"
    echo "  -c, --connections NUM   Concurrent connections (default: 10)"
    echo "  -u, --url URL          Test URL (default: Google generate_204)"
    echo "  -p, --proxy HOST:PORT  Proxy address (default: 127.0.0.1:10808)"
    echo "  -h, --help             Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 -d 120 -c 20"
    echo "  $0 -p 127.0.0.1:10809 -u https://httpbin.org/ip"
}

# Parse arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -d|--duration)
                TEST_DURATION="$2"
                shift 2
                ;;
            -c|--connections)
                CONCURRENT_CONNECTIONS="$2"
                shift 2
                ;;
            -u|--url)
                TEST_URL="$2"
                shift 2
                ;;
            -p|--proxy)
                IFS=':' read -r PROXY_HOST PROXY_PORT <<< "$2"
                shift 2
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
    
    # Check required tools
    local required_tools=("curl" "nc")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done
}

# Test proxy connectivity
test_proxy_connectivity() {
    log_info "Testing proxy connectivity..."
    
    if nc -z "$PROXY_HOST" "$PROXY_PORT" 2>/dev/null; then
        log_info "Proxy is reachable at $PROXY_HOST:$PROXY_PORT"
    else
        log_error "Cannot connect to proxy at $PROXY_HOST:$PROXY_PORT"
        exit 1
    fi
}

# Run latency test
test_latency() {
    log_info "Testing latency..."
    
    local total_time=0
    local successful_requests=0
    local failed_requests=0
    
    for i in $(seq 1 10); do
        local start_time=$(date +%s%N)
        
        if curl -s --proxy "socks5://$PROXY_HOST:$PROXY_PORT" \
                --connect-timeout 10 \
                --max-time 30 \
                "$TEST_URL" >/dev/null 2>&1; then
            local end_time=$(date +%s%N)
            local request_time=$(( (end_time - start_time) / 1000000 ))
            total_time=$((total_time + request_time))
            successful_requests=$((successful_requests + 1))
        else
            failed_requests=$((failed_requests + 1))
        fi
    done
    
    if [[ $successful_requests -gt 0 ]]; then
        local avg_latency=$((total_time / successful_requests))
        echo "Average Latency: ${avg_latency}ms"
        echo "Success Rate: $successful_requests/10 (${successful_requests}0%)"
    else
        echo "All latency tests failed"
    fi
}

# Run throughput test
test_throughput() {
    log_info "Testing throughput..."
    
    local temp_file=$(mktemp)
    local start_time=$(date +%s)
    local end_time=$((start_time + TEST_DURATION))
    local request_count=0
    local success_count=0
    
    # Function to make requests
    make_request() {
        while [[ $(date +%s) -lt $end_time ]]; do
            if curl -s --proxy "socks5://$PROXY_HOST:$PROXY_PORT" \
                    --connect-timeout 5 \
                    --max-time 10 \
                    "$TEST_URL" >/dev/null 2>&1; then
                echo "success" >> "$temp_file"
            else
                echo "failure" >> "$temp_file"
            fi
        done
    }
    
    # Start concurrent requests
    for i in $(seq 1 "$CONCURRENT_CONNECTIONS"); do
        make_request &
    done
    
    # Wait for all background processes
    wait
    
    # Calculate results
    request_count=$(wc -l < "$temp_file")
    success_count=$(grep -c "success" "$temp_file" || echo 0)
    local failure_count=$((request_count - success_count))
    
    local requests_per_second=$((request_count / TEST_DURATION))
    local success_rate=$((success_count * 100 / request_count))
    
    echo "Throughput Test Results:"
    echo "  Duration: ${TEST_DURATION}s"
    echo "  Concurrent Connections: $CONCURRENT_CONNECTIONS"
    echo "  Total Requests: $request_count"
    echo "  Successful Requests: $success_count"
    echo "  Failed Requests: $failure_count"
    echo "  Requests/Second: $requests_per_second"
    echo "  Success Rate: ${success_rate}%"
    
    # Cleanup
    rm -f "$temp_file"
}

# Test different protocols
test_protocols() {
    log_info "Testing different protocols..."
    
    local protocols=("http" "https")
    
    for protocol in "${protocols[@]}"; do
        local test_url="${protocol}://httpbin.org/ip"
        echo "Testing $protocol..."
        
        local start_time=$(date +%s%N)
        if curl -s --proxy "socks5://$PROXY_HOST:$PROXY_PORT" \
                --connect-timeout 10 \
                --max-time 30 \
                "$test_url" >/dev/null 2>&1; then
            local end_time=$(date +%s%N)
            local request_time=$(( (end_time - start_time) / 1000000 ))
            echo "  $protocol: ${request_time}ms"
        else
            echo "  $protocol: FAILED"
        fi
    done
}

# Run memory and CPU monitoring
monitor_resources() {
    log_info "Monitoring resource usage..."
    
    # Get process IDs related to StealthFlow
    local pids=$(pgrep -f "stealthflow\|xray" || echo "")
    
    if [[ -n "$pids" ]]; then
        echo "Resource Usage:"
        echo "PID    COMMAND          %CPU  %MEM"
        echo "--------------------------------"
        for pid in $pids; do
            if ps -p "$pid" >/dev/null 2>&1; then
                ps -p "$pid" -o pid,comm,%cpu,%mem --no-headers
            fi
        done
    else
        echo "No StealthFlow processes found"
    fi
}

# Generate report
generate_report() {
    log_info "Generating benchmark report..."
    
    local report_file="stealthflow_benchmark_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "StealthFlow Benchmark Report"
        echo "Generated: $(date)"
        echo "============================="
        echo ""
        echo "Configuration:"
        echo "  Proxy: $PROXY_HOST:$PROXY_PORT"
        echo "  Test URL: $TEST_URL"
        echo "  Duration: ${TEST_DURATION}s"
        echo "  Concurrent Connections: $CONCURRENT_CONNECTIONS"
        echo ""
        echo "Results:"
        test_latency
        echo ""
        test_throughput
        echo ""
        test_protocols
        echo ""
        monitor_resources
    } | tee "$report_file"
    
    log_info "Report saved to: $report_file"
}

# Main function
main() {
    echo "StealthFlow Benchmark Tool"
    echo "=========================="
    echo ""
    
    parse_arguments "$@"
    check_prerequisites
    test_proxy_connectivity
    generate_report
}

# Run main function
main "$@"
