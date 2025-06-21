#!/usr/bin/env python3
"""
StealthFlow P2P Fallback System
Clean P2P fallback system for establishing direct connections
"""

import asyncio
import json
import logging
import socket
import time
from typing import Dict, List, Optional
import aiohttp

logger = logging.getLogger('StealthFlow.P2PFallback')

class P2PFallbackSystem:
    """P2P fallback system for direct connections"""
    
    def __init__(self):
        self.discovery_endpoints = [
            "https://api.ipify.org?format=json",
            "https://httpbin.org/ip",
            "https://icanhazip.com",
        ]
        self.peer_registry = {}
        self.local_port_range = (49152, 65535)
        
    async def discover_public_ip(self) -> Optional[str]:
        """Discover public IP address"""
        for endpoint in self.discovery_endpoints:
            try:
                timeout = aiohttp.ClientTimeout(total=5)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(endpoint) as response:
                        if response.status == 200:
                            data = await response.text()
                            if endpoint.endswith('json'):
                                ip_data = json.loads(data)
                                return ip_data.get('ip', '').strip()
                            else:
                                return data.strip()
            except Exception as e:
                logger.warning(f"Failed to get IP from {endpoint}: {e}")
                continue
        return None
    
    def get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
    
    async def create_peer_connection(self, remote_peer_id: str, is_initiator: bool = True) -> Optional[dict]:
        """Create direct P2P connection"""
        try:
            public_ip = await self.discover_public_ip()
            local_ip = self.get_local_ip()
            local_port = await self.find_available_port()
            
            connection_info = {
                "peer_id": remote_peer_id,
                "public_ip": public_ip,
                "local_ip": local_ip,
                "local_port": local_port,
                "is_initiator": is_initiator,
                "timestamp": time.time()
            }
            
            if is_initiator:
                success = await self.initiate_connection(connection_info)
            else:
                success = await self.accept_connection(connection_info)
            
            if success:
                logger.info(f"P2P connection established with {remote_peer_id}")
                return connection_info
            else:
                logger.warning(f"Failed to establish P2P connection with {remote_peer_id}")
                return None
                
        except Exception as e:
            logger.error(f"P2P connection creation failed: {e}")
            return None
    
    async def find_available_port(self) -> int:
        """Find an available local port"""
        for port in range(self.local_port_range[0], self.local_port_range[1]):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        
        raise Exception("No available ports found")
    
    async def initiate_connection(self, connection_info: dict) -> bool:
        """Initiate P2P connection as client"""
        try:
            await asyncio.sleep(1)  # Simulate connection setup time
            logger.info(f"Initiated connection to {connection_info['peer_id']}")
            return True
        except Exception as e:
            logger.error(f"Connection initiation failed: {e}")
            return False
    
    async def accept_connection(self, connection_info: dict) -> bool:
        """Accept P2P connection as server"""
        try:
            await asyncio.sleep(1)  # Simulate connection setup time
            logger.info(f"Accepted connection from {connection_info['peer_id']}")
            return True
        except Exception as e:
            logger.error(f"Connection acceptance failed: {e}")
            return False
    
    async def register_peer(self, peer_id: str, peer_info: dict):
        """Register peer in local registry"""
        self.peer_registry[peer_id] = {
            **peer_info,
            "registered_at": time.time(),
            "last_seen": time.time()
        }
        logger.info(f"Registered peer {peer_id}")
    
    async def get_peer_candidates(self, country_filter: Optional[str] = None) -> List[dict]:
        """Get list of available peer candidates"""
        candidates = []
        current_time = time.time()
        
        for peer_id, peer_info in self.peer_registry.items():
            if current_time - peer_info["last_seen"] > 300:
                continue
                
            if country_filter and peer_info.get("country") != country_filter:
                continue
                
            candidates.append({
                "peer_id": peer_id,
                "country": peer_info.get("country", "unknown"),
                "bandwidth": peer_info.get("bandwidth", 0),
                "last_seen": peer_info["last_seen"]
            })
        
        candidates.sort(key=lambda x: (-x["bandwidth"], x["last_seen"]))
        return candidates

async def main():
    """Test the P2P fallback system"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    p2p_system = P2PFallbackSystem()
    
    public_ip = await p2p_system.discover_public_ip()
    local_ip = p2p_system.get_local_ip()
    
    print(f"Public IP: {public_ip}")
    print(f"Local IP: {local_ip}")
    
    await p2p_system.register_peer("test-peer-1", {
        "country": "US",
        "bandwidth": 1000,
        "ip": "192.168.1.100"
    })
    
    candidates = await p2p_system.get_peer_candidates()
    print(f"Available candidates: {len(candidates)}")

if __name__ == "__main__":
    asyncio.run(main())
