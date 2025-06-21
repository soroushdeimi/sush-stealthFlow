#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StealthFlow Profile Manager
Connection profile and multi-configuration management
"""

import json
import os
import time
import hashlib
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ProtocolType(Enum):
    """Supported protocol types"""
    VLESS_REALITY = "vless_reality"
    TROJAN = "trojan"
    SHADOWSOCKS = "shadowsocks"
    VMESS = "vmess"
    HTTP = "http"
    SOCKS5 = "socks5"

class CDNProvider(Enum):
    """CDN providers"""
    CLOUDFLARE = "cloudflare"
    AKAMAI = "akamai"
    GOOGLE = "google"
    FASTLY = "fastly"
    DIRECT = "direct"

@dataclass
class ServerConfig:
    """Server configuration"""
    address: str
    port: int
    protocol: ProtocolType
    uuid: str = ""
    password: str = ""
    host: str = ""
    path: str = ""
    sni: str = ""
    alpn: List[str] = None
    fingerprint: str = ""
    reality_public_key: str = ""
    reality_short_id: str = ""
    cdn_provider: CDNProvider = CDNProvider.DIRECT
    tls: bool = True
    flow: str = ""
    security: str = "tls"
    
    def __post_init__(self):
        if self.alpn is None:
            self.alpn = ["h2", "http/1.1"]

@dataclass
class ProfileStats:
    """Profile performance statistics"""
    total_connections: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    total_bytes_sent: int = 0
    total_bytes_received: int = 0
    avg_latency: float = 0.0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    health_score: float = 100.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_connections == 0:
            return 0.0
        return (self.successful_connections / self.total_connections) * 100

@dataclass
class Profile:
    """Complete profile including server and settings"""
    id: str
    name: str
    server_config: ServerConfig
    priority: int = 0
    enabled: bool = True
    auto_switch: bool = True
    timeout: int = 10
    retry_count: int = 3
    tags: List[str] = None
    notes: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    stats: ProfileStats = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if self.tags is None:
            self.tags = []
        if self.created_at == 0.0:
            self.created_at = time.time()
        if self.updated_at == 0.0:
            self.updated_at = time.time()
        if self.stats is None:
            self.stats = ProfileStats()

class ProfileManager:
    """Manages connection profiles and configurations"""
    
    def __init__(self, config_dir: str = None):
        self.config_dir = config_dir or os.path.expanduser("~/.stealthflow")
        self.profiles_file = os.path.join(self.config_dir, "profiles.json")
        self.backup_dir = os.path.join(self.config_dir, "backups")
        
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        self.profiles: Dict[str, Profile] = {}
        self.active_profile_id: Optional[str] = None
        self.load_profiles()
    
    def create_profile(self, name: str, server_config: ServerConfig, **kwargs) -> Profile:
        profile = Profile(
            id=str(uuid.uuid4()),
            name=name,
            server_config=server_config,
            **kwargs
        )
        
        self.profiles[profile.id] = profile
        self.save_profiles()
        
        logger.info(f"Profile created: {name} ({profile.id})")
        return profile
    
    def update_profile(self, profile_id: str, **updates) -> bool:
        if profile_id not in self.profiles:
            return False
        
        profile = self.profiles[profile_id]
        
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = time.time()
        self.save_profiles()
        
        logger.info(f"Profile updated: {profile.name} ({profile_id})")
        return True
    
    def delete_profile(self, profile_id: str) -> bool:
        """Delete profile"""
        if profile_id not in self.profiles:
            return False
        
        profile_name = self.profiles[profile_id].name
        del self.profiles[profile_id]
        
        # If active profile was deleted, activate next available profile
        if self.active_profile_id == profile_id:
            self.active_profile_id = None
            if self.profiles:
                self.set_active_profile(next(iter(self.profiles.keys())))
        
        self.save_profiles()
        logger.info(f"Profile deleted: {profile_name} ({profile_id})")
        return True
    
    def get_profile(self, profile_id: str) -> Optional[Profile]:
        """Get profile by ID"""
        return self.profiles.get(profile_id)
    
    def get_profile_by_name(self, name: str) -> Optional[Profile]:
        """Get profile by name"""
        for profile in self.profiles.values():
            if profile.name == name:
                return profile
        return None
    
    def list_profiles(self, enabled_only: bool = False) -> List[Profile]:
        """List all profiles"""
        profiles = list(self.profiles.values())
        
        if enabled_only:
            profiles = [p for p in profiles if p.enabled]
        
        # Sort by priority and name
        profiles.sort(key=lambda p: (-p.priority, p.name))
        return profiles
    
    def set_active_profile(self, profile_id: str) -> bool:
        """Set active profile"""
        if profile_id not in self.profiles:
            return False
        
        self.active_profile_id = profile_id
        self.save_profiles()
        
        profile = self.profiles[profile_id]
        logger.info(f"Active profile set: {profile.name} ({profile_id})")
        return True
    
    def get_active_profile(self) -> Optional[Profile]:
        """Get active profile"""
        if self.active_profile_id:
            return self.profiles.get(self.active_profile_id)
        return None
    
    def find_best_profile(self) -> Optional[Profile]:
        """Find best profile based on stats"""
        enabled_profiles = [p for p in self.profiles.values() if p.enabled]
        
        if not enabled_profiles:
            return None
        
        # Sort by health score and priority
        enabled_profiles.sort(
            key=lambda p: (-p.stats.health_score, -p.priority, p.stats.avg_latency)
        )
        
        return enabled_profiles[0]
    
    def update_profile_stats(self, profile_id: str, success: bool, 
                           latency: float = 0.0, bytes_sent: int = 0, 
                           bytes_received: int = 0) -> bool:
        """Update profile stats"""
        if profile_id not in self.profiles:
            return False
        
        profile = self.profiles[profile_id]
        stats = profile.stats
        
        stats.total_connections += 1
        stats.total_bytes_sent += bytes_sent
        stats.total_bytes_received += bytes_received
        
        if success:
            stats.successful_connections += 1
            stats.last_success = time.time()
            
            # Update average latency
            if stats.avg_latency == 0:
                stats.avg_latency = latency
            else:
                stats.avg_latency = (stats.avg_latency + latency) / 2
        else:
            stats.failed_connections += 1
            stats.last_failure = time.time()
        
        # Calculate health score
        self._calculate_health_score(stats)
        
        profile.updated_at = time.time()
        self.save_profiles()
        return True
    
    def _calculate_health_score(self, stats: ProfileStats) -> None:
        """Calculate profile health score"""
        score = 100.0
        
        # Reduce score based on failure rate
        failure_rate = 100 - stats.success_rate
        score -= failure_rate * 0.8
        
        # Reduce score based on latency
        if stats.avg_latency > 1000:  # more than 1 second
            score -= min(50, (stats.avg_latency - 1000) / 100)
        
        # Reduce score if recently failed
        if stats.last_failure:
            time_since_failure = time.time() - stats.last_failure
            if time_since_failure < 300:  # less than 5 minutes
                score -= 30
        
        stats.health_score = max(0, score)
    
    def import_from_url(self, url: str, name: str = None) -> Optional[Profile]:
        """Import profile from URL"""
        try:
            server_config = self._parse_proxy_url(url)
            if not server_config:
                return None
            
            if not name:
                name = f"Imported_{int(time.time())}"
            
            return self.create_profile(name, server_config)
        
        except Exception as e:
            logger.error(f"Failed to import profile from URL: {e}")
            return None
    
    def export_profile(self, profile_id: str, format: str = "json") -> Optional[str]:
        """Export profile"""
        profile = self.get_profile(profile_id)
        if not profile:
            return None
        
        if format == "json":
            return json.dumps(asdict(profile), indent=2, ensure_ascii=False)
        elif format == "url":
            return self._generate_proxy_url(profile.server_config)
        
        return None
    
    def _parse_proxy_url(self, url: str) -> Optional[ServerConfig]:
        """Parse proxy URL and convert to ServerConfig"""
        # Implement parser for different URL types
        # vless://, trojan://, ss:// etc
        
        try:
            if url.startswith("vless://"):
                return self._parse_vless_url(url)
            elif url.startswith("trojan://"):
                return self._parse_trojan_url(url)
            elif url.startswith("ss://"):
                return self._parse_shadowsocks_url(url)
            else:
                logger.warning(f"Unsupported URL scheme: {url}")
                return None
        
        except Exception as e:
            logger.error(f"Failed to parse URL {url}: {e}")
            return None
    
    def _parse_vless_url(self, url: str) -> ServerConfig:
        """Parse VLESS URL"""
        # Simple implementation - needs completion
        import urllib.parse
        
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)
        
        return ServerConfig(
            address=parsed.hostname,
            port=parsed.port or 443,
            protocol=ProtocolType.VLESS_REALITY,
            uuid=parsed.username,
            sni=query.get('sni', [''])[0],
            host=query.get('host', [''])[0],
            path=query.get('path', [''])[0]
        )
    
    def _parse_trojan_url(self, url: str) -> ServerConfig:
        """Parse Trojan URL"""
        import urllib.parse
        
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)
        
        return ServerConfig(
            address=parsed.hostname,
            port=parsed.port or 443,
            protocol=ProtocolType.TROJAN,
            password=parsed.username,
            sni=query.get('sni', [''])[0],
            host=query.get('host', [''])[0]
        )
    
    def _parse_shadowsocks_url(self, url: str) -> ServerConfig:
        """Parse Shadowsocks URL"""
        import base64
        import urllib.parse
        
        # ss://method:password@server:port
        parsed = urllib.parse.urlparse(url)
        
        return ServerConfig(
            address=parsed.hostname,
            port=parsed.port or 8388,
            protocol=ProtocolType.SHADOWSOCKS,
            password=parsed.password,
            security=parsed.username  # method
        )
    
    def _generate_proxy_url(self, config: ServerConfig) -> str:
        """Generate proxy URL from ServerConfig"""
        if config.protocol == ProtocolType.VLESS_REALITY:
            return f"vless://{config.uuid}@{config.address}:{config.port}?" \
                   f"sni={config.sni}&host={config.host}&path={config.path}"
        elif config.protocol == ProtocolType.TROJAN:
            return f"trojan://{config.password}@{config.address}:{config.port}?" \
                   f"sni={config.sni}&host={config.host}"
        
        return ""
    
    def backup_profiles(self) -> str:
        """Backup profiles"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(self.backup_dir, f"profiles_backup_{timestamp}.json")
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(self._profiles_to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Profiles backed up to: {backup_file}")
        return backup_file
    
    def restore_profiles(self, backup_file: str) -> bool:
        """Restore profiles from backup"""
        try:
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.profiles = self._dict_to_profiles(data['profiles'])
            self.active_profile_id = data.get('active_profile_id')
            
            self.save_profiles()
            logger.info(f"Profiles restored from: {backup_file}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to restore profiles: {e}")
            return False
    
    def save_profiles(self) -> None:
        """Save profiles to file"""
        try:
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(self._profiles_to_dict(), f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")
    
    def load_profiles(self) -> None:
        """Load profiles from file"""
        if not os.path.exists(self.profiles_file):
            return
        
        try:
            with open(self.profiles_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.profiles = self._dict_to_profiles(data.get('profiles', {}))
            self.active_profile_id = data.get('active_profile_id')
        
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}")
    
    def _profiles_to_dict(self) -> Dict[str, Any]:
        """Convert profiles to dictionary"""
        return {
            'profiles': {pid: asdict(profile) for pid, profile in self.profiles.items()},
            'active_profile_id': self.active_profile_id,
            'version': '1.0'
        }
    
    def _dict_to_profiles(self, profiles_dict: Dict[str, Any]) -> Dict[str, Profile]:
        """Convert dictionary to profiles"""
        profiles = {}
        
        for pid, pdata in profiles_dict.items():
            try:
                # Convert server_config
                server_data = pdata['server_config']
                server_data['protocol'] = ProtocolType(server_data['protocol'])
                server_data['cdn_provider'] = CDNProvider(server_data.get('cdn_provider', 'direct'))
                server_config = ServerConfig(**server_data)
                
                # Convert stats
                stats_data = pdata.get('stats', {})
                stats = ProfileStats(**stats_data)
                
                # Create profile
                profile_data = pdata.copy()
                profile_data['server_config'] = server_config
                profile_data['stats'] = stats
                
                profiles[pid] = Profile(**profile_data)
            
            except Exception as e:
                logger.error(f"Failed to load profile {pid}: {e}")
        
        return profiles

# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create profile manager
    pm = ProfileManager()
    
    # Create sample profile
    server = ServerConfig(
        address="example.com",
        port=443,
        protocol=ProtocolType.VLESS_REALITY,
        uuid="12345678-1234-1234-1234-123456789abc",
        sni="google.com"
    )
    
    profile = pm.create_profile("Test Server", server, priority=10)
    print(f"Created profile: {profile.name} ({profile.id})")
    
    # Test stats
    pm.update_profile_stats(profile.id, True, 150.0, 1024, 2048)
    print(f"Profile stats: {profile.stats.success_rate}% success")
    
    # Show all profiles
    for p in pm.list_profiles():
        print(f"- {p.name}: {p.stats.health_score:.1f} health score")
