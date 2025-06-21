#!/usr/bin/env python3
"""
StealthFlow Smart Client
Intelligent client with automatic protocol detection and switching
"""

import asyncio
import json
import time
import logging
import subprocess
import platform
import socket
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import aiohttp
import yaml

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('StealthFlow')

@dataclass
class ProxyProfile:
    """Represents a proxy profile configuration"""
    name: str
    protocol: str
    server: str
    port: int
    uuid: str = ""
    password: str = ""
    security: str = "auto"
    network: str = "tcp"
    reality_settings: Dict = None
    trojan_settings: Dict = None
    priority: int = 1
    latency: float = 0.0
    success_rate: float = 0.0
    last_test: float = 0.0
    enabled: bool = True

    def to_xray_config(self, local_port: int = 10808) -> Dict:
        """Convert profile to Xray configuration"""
        base_config = {
            "log": {"loglevel": "warning"},
            "inbounds": [
                {
                    "tag": "socks",
                    "port": local_port,
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

        # Configure outbound based on protocol
        if self.protocol == "vless":
            outbound = {
                "tag": "proxy",
                "protocol": "vless",
                "settings": {
                    "vnext": [
                        {
                            "address": self.server,
                            "port": self.port,
                            "users": [
                                {
                                    "id": self.uuid,
                                    "encryption": "none",
                                    "flow": "xtls-rprx-vision"
                                }
                            ]
                        }
                    ]
                },
                "streamSettings": {
                    "network": self.network,
                    "security": self.security
                }
            }
            
            if self.reality_settings:
                outbound["streamSettings"]["realitySettings"] = self.reality_settings
                
        elif self.protocol == "trojan":
            outbound = {
                "tag": "proxy",
                "protocol": "trojan",
                "settings": {
                    "servers": [
                        {
                            "address": self.server,
                            "port": self.port,
                            "password": self.password
                        }
                    ]
                },
                "streamSettings": {
                    "network": self.network,
                    "security": "tls",
                    "tlsSettings": {
                        "allowInsecure": False,
                        "serverName": self.server
                    }
                }
            }

        base_config["outbounds"] = [
            outbound,
            {"tag": "direct", "protocol": "freedom"},
            {"tag": "block", "protocol": "blackhole"}
        ]

        return base_config

class HealthChecker:
    """Connection health monitoring"""
    
    def __init__(self):        self.test_urls = [
            "https://www.google.com/generate_204",
            "https://detectportal.firefox.com/success.txt",
            "https://www.msftconnecttest.com/connecttest.txt"
        ]

    async def test_proxy(self, profile: ProxyProfile) -> Tuple[bool, float]:
        """Test proxy health"""
        try:
            # Set up temporary Xray for testing
            config = profile.to_xray_config(local_port=10900 + hash(profile.name) % 100)
            config_path = f"/tmp/test_{profile.name}.json"
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)            
            # Start Xray
            process = subprocess.Popen([
                'xray', 'run', '-config', config_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            await asyncio.sleep(2)  # Wait for startup
              # Test connection
            start_time = time.time()
            success = await self._test_connection(config["inbounds"][0]["port"])
            latency = time.time() - start_time
            
            # Terminate process
            process.terminate()
            process.wait()
            
            # Remove temporary file
            Path(config_path).unlink(missing_ok=True)
            
            return success, latency * 1000  # Convert to milliseconds
            
        except Exception as e:
            logger.error(f"Error testing {profile.name}: {e}")
            return False, 9999.0

    async def _test_connection(self, proxy_port: int) -> bool:
        """Test connection through proxy"""
        try:
            connector = aiohttp.TCPConnector()
            proxy_url = f"socks5://127.0.0.1:{proxy_port}"
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                for url in self.test_urls:
                    try:
                        async with session.get(url, proxy=proxy_url) as response:
                            if response.status == 200 or response.status == 204:
                                return True
                    except:
                        continue
                        
            return False
            
        except Exception as e:
            logger.debug(f"Connection test failed: {e}")
            return False

class ProfileManager:
    """Connection profile management"""
    
    def __init__(self, config_file: str = "stealthflow_profiles.yaml"):
        self.config_file = Path(config_file)
        self.profiles: List[ProxyProfile] = []
        self.active_profile: Optional[ProxyProfile] = None
        self.health_checker = HealthChecker()
        
    def load_profiles(self):
        """Load profiles from config file"""
        if not self.config_file.exists():
            self._create_default_config()
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            self.profiles = []
            for profile_data in data.get('profiles', []):
                profile = ProxyProfile(**profile_data)
                self.profiles.append(profile)
            logger.info(f"Loaded {len(self.profiles)} profiles")
            
        except Exception as e:
            logger.error(f"Error loading profiles: {e}")
            self._create_default_config()
    
    def save_profiles(self):
        """Save profiles to config file"""
        try:
            data = {
                'profiles': [asdict(profile) for profile in self.profiles]
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                
        except Exception as e:
            logger.error(f"Error saving profiles: {e}")
    
    def _create_default_config(self):
        """Create default configuration"""
        default_profiles = [
            ProxyProfile(
                name="REALITY-Direct",
                protocol="vless",
                server="YOUR_SERVER_IP",
                port=443,
                uuid="YOUR_UUID",
                security="reality",
                reality_settings={
                    "serverName": "www.microsoft.com",
                    "fingerprint": "chrome",
                    "show": False,
                    "publicKey": "YOUR_REALITY_PUBLIC_KEY",
                    "shortId": "YOUR_SHORT_ID",
                    "spiderX": "/"
                },
                priority=1
            ),            ProxyProfile(
                name="Trojan-CDN1",
                protocol="trojan",
                server="cdn1.yourdomain.com",
                port=443,
                password="YOUR_TROJAN_PASSWORD",
                security="tls",
                priority=2
            ),            ProxyProfile(
                name="Trojan-CDN2",
                protocol="trojan",
                server="cdn2.yourdomain.com",
                port=443,
                password="YOUR_TROJAN_PASSWORD",
                security="tls",
                priority=3
            )]
        
        self.profiles = default_profiles
        self.save_profiles()
        logger.info("Created default configuration")
        logger.warning("Please edit stealthflow_profiles.yaml with your server details")

    async def test_all_profiles(self) -> Dict[str, Tuple[bool, float]]:
        """Test all enabled profiles"""
        results = {}
        
        tasks = []
        for profile in self.profiles:
            if profile.enabled:
                task = self.health_checker.test_proxy(profile)
                tasks.append((profile.name, task))
        
        for name, task in tasks:
            try:
                success, latency = await task
                results[name] = (success, latency)
                
                # Update profile stats
                profile = next(p for p in self.profiles if p.name == name)
                profile.latency = latency
                profile.last_test = time.time()
                
                if success:
                    profile.success_rate = min(1.0, profile.success_rate + 0.1)
                else:
                    profile.success_rate = max(0.0, profile.success_rate - 0.2)
                    
            except Exception as e:
                logger.error(f"Error testing {name}: {e}")
                results[name] = (False, 9999.0)
        
        return results

    def get_best_profile(self) -> Optional[ProxyProfile]:
        """Select best profile based on stats"""
        available_profiles = [
            p for p in self.profiles 
            if p.enabled and p.success_rate > 0.5 and p.latency < 5000
        ]
        
        if not available_profiles:
            return None
            
        # Sort by priority, success rate, and latency
        available_profiles.sort(
            key=lambda p: (p.priority, -p.success_rate, p.latency)
        )
        
        return available_profiles[0]

class StealthFlowClient:
    """Main StealthFlow client"""
    
    def __init__(self):
        self.profile_manager = ProfileManager()
        self.current_process: Optional[subprocess.Popen] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.running = False
        
    async def start(self):
        """Start the client"""
        logger.info("Starting StealthFlow Client...")
        
        # Load profiles
        self.profile_manager.load_profiles()
        
        # Initial profile testing
        await self._initial_test()
        
        # Start monitoring
        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("StealthFlow Client started successfully")

    async def stop(self):
        """Stop the client"""
        logger.info("Stopping StealthFlow Client...")
        
        self.running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            
        if self.current_process:
            self.current_process.terminate()
            self.current_process.wait()
            
        logger.info("StealthFlow Client stopped")

    async def _initial_test(self):
        """Test all profiles initially"""
        logger.info("Testing all profiles...")
        
        results = await self.profile_manager.test_all_profiles()
        
        for name, (success, latency) in results.items():
            status = "OK" if success else "FAIL"
            logger.info(f"{status} {name}: {latency:.0f}ms")
        
        # Select and connect to best profile
        best_profile = self.profile_manager.get_best_profile()
        
        if best_profile:
            await self._connect_to_profile(best_profile)
        else:
            logger.error("No working profiles found!")

    async def _connect_to_profile(self, profile: ProxyProfile):
        """Connect to a specific profile"""
        try:
            # Terminate previous connection
            if self.current_process:
                self.current_process.terminate()
                self.current_process.wait()
            
            # Create Xray config
            config = profile.to_xray_config()
            config_path = Path("current_config.json")
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Run Xray
            self.current_process = subprocess.Popen([
                'xray', 'run', '-config', str(config_path)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            self.profile_manager.active_profile = profile
            
            logger.info(f"Connected to {profile.name} ({profile.latency:.0f}ms)")
            
        except Exception as e:
            logger.error(f"Error connecting to {profile.name}: {e}")

    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Test every 30 seconds
                
                if not self.running:
                    break
                
                # Test current profile
                if self.profile_manager.active_profile:
                    success, latency = await self.health_checker.test_proxy(
                        self.profile_manager.active_profile
                    )
                    
                    if not success or latency > 10000:  # If connection failed or too slow
                        logger.warning(f"Current profile failed, switching...")
                        await self._find_alternative()
                
                # Periodic test of all profiles (every 5 minutes)
                if int(time.time()) % 300 == 0:
                    await self.profile_manager.test_all_profiles()
                    self.profile_manager.save_profiles()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

    async def _find_alternative(self):
        """Find alternative connection"""
        logger.info("Looking for alternative connection...")
        
        # Quick test of profiles
        results = await self.profile_manager.test_all_profiles()
        
        # Select best option
        best_profile = self.profile_manager.get_best_profile()
        
        if best_profile and best_profile != self.profile_manager.active_profile:
            await self._connect_to_profile(best_profile)
        else:
            logger.error("No alternative connection found!")

    def get_status(self) -> Dict:
        """Get client status"""
        active = self.profile_manager.active_profile
        
        return {
            "active_profile": active.name if active else None,
            "connected": self.current_process is not None and self.current_process.poll() is None,
            "profiles": [
                {
                    "name": p.name,
                    "latency": p.latency,
                    "success_rate": p.success_rate,
                    "enabled": p.enabled
                }
                for p in self.profile_manager.profiles
            ]
        }

async def main():
    """Main function"""
    client = StealthFlowClient()
    
    try:
        await client.start()
        
        # Keep the program running
        while client.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await client.stop()

if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())
