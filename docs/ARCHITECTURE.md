# StealthFlow Architecture

## Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                    StealthFlow                          │
├─────────────────────────────────────────────────────────┤
│  Client Side              │  Server Side                │
│  ┌─────────────────────┐  │  ┌─────────────────────────┐ │
│  │ GUI/CLI Interface   │  │  │ Xray-core + Nginx      │ │
│  │ Profile Manager     │  │  │ SSL Termination         │ │
│  │ Health Monitor      │  │  │ Multi-protocol Support │ │
│  │ Auto-switcher       │  │  │ Health Endpoints        │ │
│  └─────────────────────┘  │  └─────────────────────────┘ │
│  ┌─────────────────────┐  │  ┌─────────────────────────┐ │
│  │ P2P Client          │  │  │ P2P Signaling Server    │ │
│  │ WebRTC Handler      │  │  │ Monitoring Stack        │ │
│  └─────────────────────┘  │  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Protocol Flow

### REALITY Protocol
1. Client initiates TLS handshake that mimics legitimate traffic
2. Server responds with authentic TLS certificate
3. Traffic appears as normal HTTPS to monitoring systems
4. Actual proxy data is tunneled within the TLS connection

### Trojan Protocol
1. Client sends specially formatted HTTPS requests
2. Requests include authentication headers
3. Server validates and forwards traffic
4. Works well with CDN services for additional obfuscation

### P2P Fallback
1. When traditional proxies fail, client connects to signaling server
2. WebRTC connection established with available peers
3. Traffic routed through peer-to-peer mesh network
4. Provides emergency connectivity when servers are blocked

## File Structure

```
StealthFlow/
├── client/               # Client-side code
│   ├── core/            # Core client functionality
│   │   └── stealthflow_client.py
│   ├── ui/              # GUI components
│   │   └── stealthflow_gui.py
│   └── profiles/        # Profile management
│       └── profile_manager.py
├── server/              # Server configuration templates
│   ├── configs/         # Xray and system configs
│   ├── nginx/           # Nginx configuration
│   └── scripts/         # Server management scripts
├── p2p/                 # P2P networking code
│   ├── signaling/       # WebRTC signaling server
│   └── webrtc/          # P2P client implementation
├── utils/               # Shared utilities
│   ├── config_generator.py
│   └── security.py
├── monitoring/          # Prometheus/Grafana configs
├── k8s/                 # Kubernetes manifests
├── helm/                # Helm charts
└── scripts/             # Deployment and management scripts
```

## Security Architecture

### Client Security
- Input validation for all user inputs
- Secure credential storage
- Rate limiting for connections
- TLS certificate validation
- DNS-over-HTTPS support

### Server Security
- Minimal attack surface
- Security headers and hardening
- Regular security updates
- Fail2ban integration
- Firewall configuration

### Protocol Security
- Perfect Forward Secrecy
- Certificate transparency
- Traffic obfuscation
- Anti-fingerprinting measures

## Deployment Models

### Standalone Server
- Single VPS deployment
- Manual configuration
- Direct management

### Docker Deployment
- Containerized services
- Docker Compose orchestration
- Easy scaling and updates

### Kubernetes Deployment
- Full container orchestration
- Auto-scaling capabilities
- High availability setup
- Integrated monitoring

### Development Environment
- Local testing setup
- Mock services
- Debug configuration
