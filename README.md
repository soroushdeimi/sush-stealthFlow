# StealthFlow

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos-lightgrey.svg)](https://github.com/soroushdeimi/sush-stealthFlow)

StealthFlow is a smart proxy client/server system that increases censorship resilience by combining multiple protocols and transport layers. It uses an intelligent client to automatically switch between REALITY, Trojan over CDN, and a P2P fallback network based on real-time health checks.

## Core Features

- **Multi-Protocol Support**: REALITY (undetectable TLS), Trojan (CDN-friendly), and P2P WebRTC fallback
- **Intelligent Switching**: Real-time health monitoring with automatic failover between protocols
- **Production Ready**: Docker, Kubernetes, and Helm chart support with monitoring stack
- **Developer Friendly**: Clean Python codebase with comprehensive API and extensive logging
- **Security Focused**: Input validation, rate limiting, perfect forward secrecy, and security auditing

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Client         │    │  Server          │    │  P2P Network    │
│  ┌───────────┐  │    │  ┌────────────┐  │    │  ┌───────────┐  │
│  │    GUI    │  │    │  │ Xray-core  │  │    │  │ Signaling │  │
│  │    CLI    │  │◄───┤  │   Nginx    │  ├────┤  │  Server   │  │
│  │ Profiles  │  │    │  │    SSL     │  │    │  │  WebRTC   │  │
│  └───────────┘  │    │  └────────────┘  │    │  └───────────┘  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Quick Start

### Server (VPS with domain)
```bash
curl -sSL https://raw.githubusercontent.com/soroushdeimi/sush-stealthFlow/main/setup.sh | \
  bash -s -- -t server -d yourdomain.com -e admin@yourdomain.com
```

### Client (Local machine)
```bash
git clone https://github.com/soroushdeimi/sush-stealthFlow.git
cd sush-stealthFlow
pip install -r requirements.txt
python stealthflow.py setup
python stealthflow.py gui
```

### Docker Deployment
```bash
git clone https://github.com/soroushdeimi/sush-stealthFlow.git
cd sush-stealthFlow
cp .env.example .env
# Edit .env with your domain and email
docker-compose up -d
```

## Documentation

- **[Installation Guide](docs/SERVER_INSTALL.md)** - Complete server setup instructions
- **[Client Setup](docs/CLIENT_INSTALL.md)** - Client installation and configuration
- **[Usage Guide](docs/USAGE.md)** - Day-to-day operations and commands
- **[FAQ](docs/FAQ.md)** - Frequently asked questions
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Architecture](docs/ARCHITECTURE.md)** - Technical architecture overview
- **[Security](SECURITY.md)** - Security considerations and reporting

## Requirements

### Server
- Linux VPS (Ubuntu 18.04+ recommended)
- Domain name (optional but recommended)
- 512MB RAM minimum, 1GB+ recommended
- Ports 80, 443 accessible

### Client
- Python 3.8+
- Windows, macOS, or Linux
- 50MB disk space

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
git clone https://github.com/soroushdeimi/sush-stealthFlow.git
cd sush-stealthFlow
pip install -r requirements.txt
pip install -r requirements-dev.txt
python -m pytest tests/
```

## Security

- Zero-logging policy on proxy traffic
- Regular security audits and dependency updates
- Input validation and rate limiting
- Perfect forward secrecy with rotating keys

**Security Issues**: Please email security@stealthflow.org instead of creating public issues.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: [GitHub Issues](https://github.com/soroushdeimi/sush-stealthFlow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/soroushdeimi/sush-stealthFlow/discussions)
---

*StealthFlow is designed to help people access information freely. Please use it responsibly and in accordance with your local laws.*
