#!/usr/bin/env python3
"""
StealthFlow Project Launcher
Smart Anti-Censorship Tool Launcher

This script allows you to easily run different StealthFlow components:
- GUI Client
- CLI Client  
- P2P Signaling Server
- Management Tools
"""

import sys
import os
import argparse
import subprocess
import json
from pathlib import Path

# Add project path to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_requirements():
    """Check for required dependencies"""
    try:
        import yaml
        import aiohttp
        import asyncio
    except ImportError as e:
        print(f"Error: Required dependency not installed: {e}")
        print("To install dependencies run:")
        print("pip install -r requirements.txt")
        return False
    
    # Check Xray
    try:
        result = subprocess.run(['xray', 'version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("Warning: Xray not installed or not in PATH")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("Warning: Xray not installed or not in PATH")
        return False
    
    return True

def run_client_gui():
    """Run GUI client"""
    print("Starting StealthFlow GUI client...")
    
    gui_path = PROJECT_ROOT / "client" / "ui" / "stealthflow_gui.py"
    if not gui_path.exists():
        print(f"GUI file not found: {gui_path}")
        return 1
    
    try:
        subprocess.run([sys.executable, str(gui_path)], check=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error running GUI: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nExiting program")
        return 0

def run_client_cli():
    """Run CLI client"""
    print("Starting StealthFlow CLI client...")
    
    cli_path = PROJECT_ROOT / "client" / "core" / "stealthflow_client.py"
    if not cli_path.exists():
        print(f"CLI file not found: {cli_path}")
        return 1
    
    try:
        subprocess.run([sys.executable, str(cli_path)], check=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error running CLI: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nExiting program")
        return 0

def run_p2p_signaling():
    """Run P2P signaling server"""
    print("Starting P2P signaling server...")
    
    signaling_path = PROJECT_ROOT / "p2p" / "signaling" / "signaling_server.py"
    if not signaling_path.exists():
        print(f"Signaling file not found: {signaling_path}")
        return 1
    
    try:
        subprocess.run([sys.executable, str(signaling_path)], check=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error running signaling server: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nStopping signaling server")
        return 0

def run_p2p_helper():
    """Run P2P helper"""
    print("Starting P2P Helper...")
    
    p2p_path = PROJECT_ROOT / "p2p" / "webrtc" / "p2p_fallback.py"
    if not p2p_path.exists():
        print(f"P2P file not found: {p2p_path}")
        return 1
    
    try:
        subprocess.run([sys.executable, str(p2p_path), "helper"], check=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error running P2P Helper: {e}")
        return 1
    except KeyboardInterrupt:
        print("\nStopping P2P Helper")
        return 0

def generate_config():
    """Generate client configuration with input validation"""
    print("Starting secure config generation...")
    
    # Add security import
    try:
        from utils.security import InputValidator, sanitize_log_message
    except ImportError:
        print("Warning: Using basic validation")
        class InputValidator:
            @staticmethod
            def validate_server_address(addr): return bool(addr and len(addr) < 200)
            @staticmethod
            def validate_port(port): 
                try: return 1 <= int(port) <= 65535
                except: return False
            @staticmethod
            def validate_uuid(uuid): return bool(uuid and len(uuid) > 20)
            @staticmethod
            def validate_password(pwd): return bool(pwd and len(pwd) >= 8)
    
    generator_path = PROJECT_ROOT / "utils" / "config_generator.py"
    if not generator_path.exists():
        print(f"Config generator not found: {generator_path}")
        return 1
    
    # Get and validate information from user
    config_type = input("Config type (reality/trojan/ss): ").strip().lower()
    if config_type not in ['reality', 'trojan', 'ss']:
        print("Error: Invalid config type. Must be reality, trojan, or ss")
        return 1
    
    server = input("Server address: ").strip()
    if not server or not InputValidator.validate_server_address(server):
        print("Error: Invalid server address format")
        return 1
    
    port_input = input("Port (default 443): ").strip() or "443"
    if not InputValidator.validate_port(port_input):
        print("Error: Invalid port number. Must be between 1-65535")
        return 1
    
    try:
        if config_type == "reality":
            uuid = input("UUID: ").strip()
            if not uuid or not InputValidator.validate_uuid(uuid):
                print("Error: Invalid UUID format")
                return 1
            
            public_key = input("Public Key: ").strip()
            if not public_key or len(public_key) < 20:
                print("Error: Invalid public key")
                return 1
            
            short_id = input("Short ID: ").strip()
            if not short_id or len(short_id) < 4:
                print("Error: Invalid short ID")
                return 1
            
            cmd = [sys.executable, str(generator_path), 
                   "--type", "reality", "--server", server, "--port", port_input,
                   "--uuid", uuid, "--public-key", public_key, "--short-id", short_id,
                   "--share-url"]
        
        elif config_type in ["trojan", "ss"]:
            password = input("Password: ").strip()
            if not password or not InputValidator.validate_password(password):
                print("Error: Invalid password. Must be at least 8 characters")
                return 1
            
            cmd = [sys.executable, str(generator_path), 
                   "--type", config_type, "--server", server, "--port", port_input,
                   "--password", password, "--share-url"]
        
        print("Generating configuration...")
        subprocess.run(cmd, check=True)
        print("Configuration generated successfully!")
        return 0
        
    except subprocess.CalledProcessError as e:
        print(f"Config generation error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

def run_tests():
    """Run tests"""
    print("Running StealthFlow tests...")
    
    test_path = PROJECT_ROOT / "tests" / "test_stealthflow.py"
    if not test_path.exists():
        print(f"Test file not found: {test_path}")
        return 1
    
    try:
        subprocess.run([sys.executable, str(test_path)], check=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Test execution error: {e}")
        return 1

def show_status():
    """Show system status"""
    print("StealthFlow System Status")
    print("=" * 40)
    
    # Check Python
    print(f"Python: {sys.version.split()[0]}")
    
    # Check Xray
    try:
        result = subprocess.run(['xray', 'version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"Xray: {version_line}")
        else:
            print("Xray: Not installed")
    except:
        print("Xray: Not installed")
    
    # Check config files
    profiles_file = PROJECT_ROOT / "stealthflow_profiles.yaml"
    if profiles_file.exists():
        print("Profiles file: Available")
    else:
        print("Profiles file: Not found")
    
    settings_file = PROJECT_ROOT / "stealthflow_settings.json"
    if settings_file.exists():
        print("Settings file: Available")
    else:
        print("Settings file: Not found")
    
    # Check Python dependencies
    try:
        import yaml, aiohttp, websockets
        print("Python dependencies: Installed")
    except ImportError:
        print("Python dependencies: Not installed")

def setup_project():
    """Initial project setup"""
    print("Setting up project...")
    
    # Create default config files
    profiles_file = PROJECT_ROOT / "stealthflow_profiles.yaml"
    if not profiles_file.exists():
        print("Creating sample profiles file...")
        
        sample_profiles = """profiles:
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
"""
        
        with open(profiles_file, 'w', encoding='utf-8') as f:
            f.write(sample_profiles)
        print(f"Profiles file created: {profiles_file}")
    
    # Create settings file
    settings_file = PROJECT_ROOT / "stealthflow_settings.json"
    if not settings_file.exists():
        print("Creating sample settings file...")
        
        sample_settings = {
            "socks_port": 10808,
            "http_port": 10809,
            "test_interval": 30,
            "max_latency": 5000,
            "retry_count": 3,
            "use_doh": True,
            "dns_servers": [
                "https://dns.google/dns-query",
                "https://cloudflare-dns.com/dns-query"
            ],
            "auto_switch": True,
            "log_level": "INFO",
            "p2p_signaling_server": "wss://signaling.stealthflow.org"
        }
        
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(sample_settings, f, indent=2, ensure_ascii=False)
        print(f"Settings file created: {settings_file}")
    
    print("Setup completed!")
    print("\nNext steps:")
    print("1. Edit stealthflow_profiles.yaml file")
    print("2. Enter your server information")  
    print("3. Start with 'python stealthflow.py gui'")

def main():
    """Main function"""
    
    # Logo
    print("""
███████╗████████╗███████╗ █████╗ ██╗  ████████╗██╗  ██╗███████╗██╗      ██████╗ ██╗    ██╗
██╔════╝╚══██╔══╝██╔════╝██╔══██╗██║  ╚══██╔══╝██║  ██║██╔════╝██║     ██╔═══██╗██║    ██║
███████╗   ██║   █████╗  ███████║██║     ██║   ███████║█████╗  ██║     ██║   ██║██║ █╗ ██║
╚════██║   ██║   ██╔══╝  ██╔══██║██║     ██║   ██╔══██║██╔══╝  ██║     ██║   ██║██║███╗██║
███████║   ██║   ███████╗██║  ██║███████╗██║   ██║  ██║██║     ███████╗╚██████╔╝╚███╔███╔╝
╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝  ╚══╝╚══╝ 
    """)
    
    print("StealthFlow - Smart Anti-Censorship System")
    print("=" * 60)
    
    parser = argparse.ArgumentParser(
        description="StealthFlow Project Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python stealthflow.py gui              # Run GUI interface
  python stealthflow.py cli              # Run command line
  python stealthflow.py p2p-signaling    # Run signaling server
  python stealthflow.py p2p-helper       # Run P2P helper
  python stealthflow.py config           # Generate new config
  python stealthflow.py setup            # Initial setup
  python stealthflow.py status           # Show status
  python stealthflow.py test             # Run tests
        """
    )
    
    parser.add_argument(
        'command', 
        choices=['gui', 'cli', 'p2p-signaling', 'p2p-helper', 'config', 'test', 'status', 'setup'],
        help='Command to run'
    )
    
    parser.add_argument(
        '--skip-requirements', 
        action='store_true',
        help='Skip dependency check'
    )
    
    args = parser.parse_args()
    
    # Check dependencies
    if not args.skip_requirements and args.command not in ['status', 'setup']:
        if not check_requirements():
            print("\nPlease install dependencies first:")
            print("pip install -r requirements.txt")
            return 1
    
    # Set working directory
    os.chdir(PROJECT_ROOT)
    
    # Execute command
    if args.command == 'gui':
        return run_client_gui()
    elif args.command == 'cli':
        return run_client_cli()
    elif args.command == 'p2p-signaling':
        return run_p2p_signaling()
    elif args.command == 'p2p-helper':
        return run_p2p_helper()
    elif args.command == 'config':
        return generate_config()
    elif args.command == 'test':
        return run_tests()
    elif args.command == 'status':
        show_status()
        return 0
    elif args.command == 'setup':
        setup_project()
        return 0
    else:
        print(f"Invalid command: {args.command}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nExiting program")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
