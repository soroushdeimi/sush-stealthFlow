#!/usr/bin/env python3
"""
StealthFlow Configuration Generator
Automated client configuration generator for StealthFlow
"""

import json
import uuid
import argparse
import base64
import urllib.parse
from typing import Dict, List

class ConfigGenerator:
    """Configuration generator class"""
    
    def __init__(self):
        self.base_config = {
            "log": {"loglevel": "warning"},
            "inbounds": [
                {
                    "tag": "socks",
                    "port": 10808,
                    "listen": "127.0.0.1",
                    "protocol": "socks",
                    "sniffing": {
                        "enabled": True,
                        "destOverride": ["http", "tls"]
                    },
                    "settings": {
                        "auth": "noauth",
                        "udp": True
                    }
                },
                {
                    "tag": "http",
                    "port": 10809,
                    "listen": "127.0.0.1",
                    "protocol": "http",
                    "sniffing": {
                        "enabled": True,
                        "destOverride": ["http", "tls"]
                    }
                }
            ],
            "outbounds": [],
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "rules": [
                    {
                        "type": "field",
                        "ip": ["geoip:private"],
                        "outboundTag": "direct"
                    },                    {
                        "type": "field",
                        "domain": ["geosite:category-ads-all"],
                        "outboundTag": "block"
                    }
                ]
            }
        }

    def generate_reality_config(self, server_ip: str, uuid_str: str, public_key: str,
                              short_id: str, server_name: str = "www.microsoft.com") -> Dict:
        """Generate REALITY configuration"""
        config = self.base_config.copy()
        
        outbound = {
            "tag": "proxy",
            "protocol": "vless",
            "settings": {
                "vnext": [
                    {
                        "address": server_ip,
                        "port": 443,
                        "users": [
                            {
                                "id": uuid_str,
                                "encryption": "none",
                                "flow": "xtls-rprx-vision"
                            }
                        ]
                    }
                ]
            },
            "streamSettings": {
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "serverName": server_name,
                    "fingerprint": "chrome",
                    "show": False,
                    "publicKey": public_key,
                    "shortId": short_id,
                    "spiderX": "/"
                }
            }
        }
        
        config["outbounds"] = [
            outbound,
            {"tag": "direct", "protocol": "freedom"},
            {"tag": "block", "protocol": "blackhole"}
        ]
        
        return config

    def generate_trojan_config(self, server_domain: str, password: str, port: int = 443) -> Dict:
        """Generate Trojan configuration"""
        config = self.base_config.copy()
        
        outbound = {
            "tag": "proxy",
            "protocol": "trojan",
            "settings": {
                "servers": [
                    {
                        "address": server_domain,
                        "port": port,
                        "password": password
                    }
                ]
            },
            "streamSettings": {
                "network": "tcp",
                "security": "tls",
                "tlsSettings": {
                    "allowInsecure": False,
                    "serverName": server_domain,
                    "alpn": ["h2", "http/1.1"]
                }
            }
        }
        
        config["outbounds"] = [
            outbound,
            {"tag": "direct", "protocol": "freedom"},
            {"tag": "block", "protocol": "blackhole"}
        ]
        
        return config

    def generate_shadowsocks_config(self, server: str, port: int, password: str, 
                                  method: str = "chacha20-ietf-poly1305") -> Dict:
        """Generate Shadowsocks configuration"""
        config = self.base_config.copy()
        
        outbound = {
            "tag": "proxy",
            "protocol": "shadowsocks",
            "settings": {
                "servers": [
                    {
                        "address": server,
                        "port": port,
                        "password": password,
                        "method": method
                    }
                ]
            }
        }
        
        config["outbounds"] = [
            outbound,
            {"tag": "direct", "protocol": "freedom"},
            {"tag": "block", "protocol": "blackhole"}
        ]
        
        return config

    def generate_multi_config(self, configs: List[Dict], priorities: List[int] = None) -> Dict:
        """Generate multi-configuration with failover"""
        if not configs:
            raise ValueError("At least one configuration is required")
        
        if priorities is None:
            priorities = list(range(len(configs)))
        
        base_config = self.base_config.copy()
        
        # Combine all outbounds
        outbounds = []
        
        for i, config in enumerate(configs):
            proxy_outbound = next(
                (ob for ob in config["outbounds"] if ob["tag"] == "proxy"),
                None
            )
            if proxy_outbound:
                # Change tag name to prevent conflicts
                proxy_outbound["tag"] = f"proxy_{i}"
                outbounds.append(proxy_outbound)
        
        # Add base outbounds
        outbounds.extend([
            {"tag": "direct", "protocol": "freedom"},
            {"tag": "block", "protocol": "blackhole"}
        ])
        
        base_config["outbounds"] = outbounds
        
        # Configure routing for failover
        routing_rules = []
        
        # Base rules
        routing_rules.extend([
            {
                "type": "field",
                "ip": ["geoip:private"],
                "outboundTag": "direct"
            },
            {
                "type": "field",
                "domain": ["geosite:category-ads-all"],
                "outboundTag": "block"
            }
        ])
        
        base_config["routing"]["rules"] = routing_rules
        
        return base_config

    def generate_share_url(self, config_type: str, **kwargs) -> str:
        """Generate subscription URL"""
        if config_type == "vless":
            return self._generate_vless_url(**kwargs)
        elif config_type == "trojan":
            return self._generate_trojan_url(**kwargs)
        elif config_type == "ss":
            return self._generate_shadowsocks_url(**kwargs)
        else:
            raise ValueError(f"Unsupported config type: {config_type}")

    def _generate_vless_url(self, server: str, port: int, uuid_str: str, public_key: str,
                           short_id: str, server_name: str = "www.microsoft.com", 
                           remark: str = "StealthFlow-REALITY") -> str:
        """Generate VLESS/REALITY URL"""
        params = {
            "encryption": "none",
            "flow": "xtls-rprx-vision",
            "security": "reality",
            "sni": server_name,
            "fp": "chrome",
            "pbk": public_key,
            "sid": short_id,
            "type": "tcp",
            "headerType": "none"
        }
        
        query_string = urllib.parse.urlencode(params)
        url = f"vless://{uuid_str}@{server}:{port}?{query_string}#{urllib.parse.quote(remark)}"
        
        return url

    def _generate_trojan_url(self, server: str, port: int, password: str,
                           remark: str = "StealthFlow-Trojan") -> str:
        """Generate Trojan URL"""
        params = {
            "security": "tls",
            "type": "tcp",
            "headerType": "none",
            "sni": server
        }
        
        query_string = urllib.parse.urlencode(params)
        url = f"trojan://{password}@{server}:{port}?{query_string}#{urllib.parse.quote(remark)}"
        
        return url

    def _generate_shadowsocks_url(self, server: str, port: int, password: str,
                                method: str = "chacha20-ietf-poly1305",
                                remark: str = "StealthFlow-SS") -> str:
        """Generate Shadowsocks URL"""
        user_info = f"{method}:{password}"
        encoded_user_info = base64.b64encode(user_info.encode()).decode()
        
        url = f"ss://{encoded_user_info}@{server}:{port}#{urllib.parse.quote(remark)}"
        return url

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="StealthFlow Config Generator")
    parser.add_argument("--type", choices=["reality", "trojan", "ss"], required=True,
                      help="Config type")
    parser.add_argument("--server", required=True, help="Server address")
    parser.add_argument("--port", type=int, default=443, help="Server port")
    parser.add_argument("--output", help="Output file")
    parser.add_argument("--share-url", action="store_true", help="Generate subscription URL")
    
    # REALITY parameters
    parser.add_argument("--uuid", help="UUID for REALITY")
    parser.add_argument("--public-key", help="REALITY public key")
    parser.add_argument("--short-id", help="Short ID for REALITY")
    parser.add_argument("--server-name", default="www.microsoft.com", 
                      help="Server name for REALITY")
    
    # Trojan/SS parameters
    parser.add_argument("--password", help="Password for Trojan/Shadowsocks")
    parser.add_argument("--method", default="chacha20-ietf-poly1305",
                      help="Encryption method for Shadowsocks")
    
    args = parser.parse_args()
    
    generator = ConfigGenerator()
    
    try:
        if args.type == "reality":
            if not all([args.uuid, args.public_key, args.short_id]):
                print("Error: REALITY requires UUID, public-key and short-id")
                return
            
            config = generator.generate_reality_config(
                args.server, args.uuid, args.public_key, 
                args.short_id, args.server_name
            )
            
            if args.share_url:
                url = generator.generate_share_url(
                    "vless", server=args.server, port=args.port,
                    uuid_str=args.uuid, public_key=args.public_key,
                    short_id=args.short_id, server_name=args.server_name
                )
                print(f"Share URL: {url}")
                
        elif args.type == "trojan":
            if not args.password:
                print("Error: Trojan requires password")
                return
            
            config = generator.generate_trojan_config(
                args.server, args.password, args.port
            )
            
            if args.share_url:
                url = generator.generate_share_url(
                    "trojan", server=args.server, port=args.port,
                    password=args.password
                )
                print(f"Share URL: {url}")
                
        elif args.type == "ss":
            if not args.password:
                print("Error: Shadowsocks requires password")
                return
            
            config = generator.generate_shadowsocks_config(
                args.server, args.port, args.password, args.method
            )
            
            if args.share_url:
                url = generator.generate_share_url(
                    "ss", server=args.server, port=args.port,
                    password=args.password, method=args.method
                )
                print(f"Share URL: {url}")
        
        # Save config
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"Config saved to {args.output}")
        else:
            print(json.dumps(config, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
