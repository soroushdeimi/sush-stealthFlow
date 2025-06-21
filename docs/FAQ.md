# Frequently Asked Questions

## General Questions

**Q: Is this actually secure? Can it be detected?**
A: StealthFlow uses REALITY and Trojan protocols that are designed to be extremely difficult to detect. REALITY traffic looks exactly like legitimate HTTPS traffic to real websites. However, no proxy is 100% undetectable - we just make it much harder.

**Q: Why not just use a VPN?**
A: Traditional VPNs are easy to block because they have obvious traffic patterns. StealthFlow's traffic looks like normal web browsing, making it much harder to detect and block.

**Q: Do I need a domain name?**
A: For best results, yes. But StealthFlow can work with just an IP address too. Having a domain makes your traffic look more legitimate and enables automatic SSL certificates.

**Q: How much does it cost to run?**
A: Just the cost of a VPS (usually $5-20/month depending on your needs). StealthFlow itself is completely free and open source.

**Q: Can multiple people use the same server?**
A: Absolutely! The server can handle multiple users. Use `sudo stealthflow-admin add-user username` to create additional user configurations.

## Technical Questions

**Q: What protocols does StealthFlow support?**
A: Currently REALITY (VLESS) and Trojan. We're working on adding more protocols based on community feedback.

**Q: How does the P2P fallback work?**
A: When your main proxies fail, StealthFlow can establish WebRTC connections to other users running the P2P helper. It's like a mesh network for emergency connectivity.

**Q: Can I use this for torrenting?**
A: While technically possible, please be respectful of your VPS provider's terms of service and don't abuse the bandwidth.

**Q: How much bandwidth does it use?**
A: Only what you actually browse. There's no constant overhead like some VPN solutions.

**Q: Is IPv6 supported?**
A: Yes, StealthFlow works with IPv6. The setup script auto-detects and configures both IPv4 and IPv6.

## Setup Issues

**Q: The setup script failed. What now?**
A: Check the logs: `sudo journalctl -u stealthflow` and look for error messages. Common issues:
- Firewall blocking ports 80/443
- Domain not pointing to your server IP
- Insufficient permissions (did you use sudo?)

**Q: I can connect but internet is slow. Help?**
A: Try these steps:
1. Test different profiles (`python stealthflow.py cli --speed-test`)
2. Check your VPS location (closer is usually better)
3. Try switching protocols in the GUI
4. Check if your VPS provider has bandwidth limits

**Q: Connection works sometimes but not others.**
A: This often happens when censorship systems are adaptive. StealthFlow's auto-switching should handle this, but you can also:
1. Enable P2P fallback
2. Set up multiple server profiles
3. Check the health monitor logs

**Q: How do I update StealthFlow?**
A: 
```bash
cd sush-stealthFlow
git pull
sudo ./setup.sh --update
```
