# StealthFlow Client Installation Guide

## Prerequisites

### Supported Operating Systems
- **Windows**: 10/11 (x64)
- **macOS**: 10.15+ (Intel/Apple Silicon)
- **Linux**: Ubuntu 20.04+, Debian 11+, CentOS 8+

### Required Software
- Python 3.8+
- pip (usually installed with Python)
- Git (optional)

## Automatic Installation (Recommended)

### Windows

1. **Download PowerShell Script**:
```powershell
# Run in PowerShell (Run as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/username/stealthflow/main/client/install-client.ps1" -OutFile "install-client.ps1"
.\install-client.ps1
```

2. **Or use WSL**:
```bash
curl -sSL https://raw.githubusercontent.com/username/stealthflow/main/client/install-client.sh | bash
```

### macOS/Linux

```bash
# Download and run installation script
curl -sSL https://raw.githubusercontent.com/username/stealthflow/main/client/install-client.sh | bash
```

## Manual Installation

### Step 1: Install Python and dependencies

#### Windows
```powershell
# Install Python from Microsoft Store or python.org
# Then install pip packages
pip install -r requirements.txt
```

#### macOS
```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python3

# Install pip packages
pip3 install -r requirements.txt
```

#### Linux (Ubuntu/Debian)
```bash
# Install Python and pip
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# Install pip packages
pip3 install -r requirements.txt
```

### Step 2: Install Xray-core

#### Windows
```powershell
# Download from GitHub
$XrayVersion = (Invoke-RestMethod -Uri "https://api.github.com/repos/XTLS/Xray-core/releases/latest").tag_name
$XrayUrl = "https://github.com/XTLS/Xray-core/releases/download/$XrayVersion/Xray-windows-64.zip"

# Download and extract
Invoke-WebRequest -Uri $XrayUrl -OutFile "Xray-windows-64.zip"
Expand-Archive -Path "Xray-windows-64.zip" -DestinationPath "C:\Program Files\Xray"

# Add to PATH
$env:PATH += ";C:\Program Files\Xray"
[Environment]::SetEnvironmentVariable("PATH", $env:PATH, [EnvironmentVariableTarget]::User)
```

#### macOS/Linux
```bash
# Detect architecture
ARCH=$(uname -m)
case $ARCH in
    x86_64) XRAY_ARCH="64" ;;
    aarch64|arm64) XRAY_ARCH="arm64-v8a" ;;
    *) echo "Architecture not supported: $ARCH"; exit 1 ;;
esac

# Download latest version
XRAY_VERSION=$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases/latest | grep tag_name | cut -d '"' -f 4)

if [[ "$OSTYPE" == "darwin"* ]]; then
    wget "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/Xray-macos-${XRAY_ARCH}.zip"
    unzip "Xray-macos-${XRAY_ARCH}.zip"
else
    wget "https://github.com/XTLS/Xray-core/releases/download/${XRAY_VERSION}/Xray-linux-${XRAY_ARCH}.zip"
    unzip "Xray-linux-${XRAY_ARCH}.zip"
fi

# Install
sudo mv xray /usr/local/bin/
sudo chmod +x /usr/local/bin/xray
```

### Step 3: Download StealthFlow

```bash
# Clone repository
git clone https://github.com/soroushdeimi/sush-stealthFlow.git
cd sush-stealthFlow

# Or download ZIP
wget https://github.com/soroushdeimi/sush-stealthFlow/archive/main.zip
unzip main.zip
cd sush-stealthFlow-main
```

### Step 4: Setup Python environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### Step 1: Create profile file

Create `stealthflow_profiles.yaml` file in the main directory:

```yaml
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

  - name: "Trojan-CDN2"
    protocol: "trojan"
    server: "cdn2.yourdomain.com"
    port: 443
    password: "YOUR_TROJAN_PASSWORD"
    security: "tls"
    priority: 3
    enabled: true

  - name: "Trojan-CDN3"
    protocol: "trojan"
    server: "cdn3.yourdomain.com"
    port: 443
    password: "YOUR_TROJAN_PASSWORD"
    security: "tls"
    priority: 4
    enabled: true
```

### Step 2: Advanced settings (Optional)

Create `stealthflow_settings.json` file for advanced settings:

```json
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
```

## Run

### Method 1: Graphical Interface (GUI)

#### Windows
```powershell
# Activate virtual environment
venv\Scripts\activate

# Run GUI
python client\ui\stealthflow_gui.py
```

#### macOS/Linux
```bash
# Activate virtual environment
source venv/bin/activate

# Run GUI
python3 client/ui/stealthflow_gui.py
```

### Method 2: Command Line (CLI)

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Run CLI
python3 client/core/stealthflow_client.py
```

### Method 3: P2P Helper

```bash
# Run as P2P helper
python3 p2p/webrtc/p2p_fallback.py helper
```

## Usage

### Initial Connection

1. **Open the GUI**
2. **Click on the "Connection" tab**
3. **Press the "Connect" button**
4. **Wait for the best profile to be selected**

### Browser Proxy Setup

After successful connection, proxy is available at:
- **SOCKS5**: `127.0.0.1:10808`
- **HTTP**: `127.0.0.1:10809`

#### Chrome/Edge
1. Settings → Advanced → System → Open proxy settings
2. Manual proxy configuration
3. SOCKS Host: `127.0.0.1`, Port: `10808`

#### Firefox
1. Settings → Network Settings
2. Manual proxy configuration
3. SOCKS Host: `127.0.0.1`, Port: `10808`, SOCKS v5

### Monitoring and Management

- **Test Connections**: "Test Connections" button in GUI
- **Change Profile**: In "Profiles" tab
- **Enable P2P**: In "P2P Fallback" tab
- **View Logs**: In "Logs" tab

## Troubleshooting

### Common Issues

#### "xray command not found"
```bash
# Check Xray installation
which xray
xray version

# If not installed, reinstall
```

#### "Connection failed"
1. Check server information in profile
2. Test internet connection
3. Check firewall
4. Direct test with `telnet server_ip 443`

#### "Python module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### GUI issues on Linux
```bash
# Install tkinter
sudo apt install python3-tk

# Install GUI dependencies
sudo apt install python3-pil python3-pil.imagetk
```

### Logs and Debug

#### Enable detailed logging
```python
# In stealthflow_settings.json file
{
  "log_level": "DEBUG"
}
```

#### Log paths
- **Windows**: `%APPDATA%\StealthFlow\logs\`
- **macOS**: `~/Library/Logs/StealthFlow/`
- **Linux**: `~/.local/share/StealthFlow/logs/`

### Manual Connection Testing

```bash
# Test SOCKS5 with curl
curl --socks5 127.0.0.1:10808 http://httpbin.org/ip

# Test HTTP proxy
curl --proxy http://127.0.0.1:10809 http://httpbin.org/ip
```

## Updates

### Automatic
```bash
# Future: Update button in GUI
```

### Manual
```bash
# Download new version
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade
```

## Uninstall

### Windows
```powershell
# Remove program folder
Remove-Item -Recurse -Force "C:\Program Files\StealthFlow"

# Remove user settings
Remove-Item -Recurse -Force "$env:APPDATA\StealthFlow"
```

### macOS/Linux
```bash
# Remove program folder
rm -rf ~/StealthFlow

# Remove symlinks
sudo rm -f /usr/local/bin/stealthflow-*

# Remove settings
rm -rf ~/.local/share/StealthFlow
```

## FAQ

### Is StealthFlow free?
Yes, StealthFlow is completely free and open source.

### How is it different from other VPNs?
StealthFlow uses multiple advanced technologies and automatically switches to alternative methods when blocked.

### Does it support mobile?
Currently a desktop version is provided. Mobile version is in development.

### Is it secure?
Yes, all traffic is encrypted and no logs are stored.

