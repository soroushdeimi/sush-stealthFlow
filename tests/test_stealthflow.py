#!/usr/bin/env python3
"""
StealthFlow Test Suite
Automated test suite for StealthFlow
"""

import asyncio
import unittest
import json
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Add project path to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.core.stealthflow_client import StealthFlowClient, HealthChecker
from client.profiles.profile_manager import ProfileManager, Profile, ServerConfig, ProtocolType
from utils.config_generator import ConfigGenerator
from p2p.webrtc.p2p_fallback import P2PManager

class TestProfile(unittest.TestCase):
    """Test Profile class"""
    
    def setUp(self):
        """Setup before each test"""
        self.reality_server = ServerConfig(
            address="127.0.0.1",
            port=443,
            protocol=ProtocolType.VLESS_REALITY,
            uuid="12345678-1234-1234-1234-123456789012",
            reality_public_key="test_public_key",
            reality_short_id="test_short_id",
            sni="www.example.com"
        )
        
        self.reality_profile = Profile(
            name="test-reality",
            config=self.reality_server
        )
        
        self.trojan_server = ServerConfig(
            address="example.com",
            port=443,
            protocol=ProtocolType.TROJAN,
            password="test_password"
        )
        
        self.trojan_profile = Profile(
            name="test-trojan",
            config=self.trojan_server
        )
    
    def test_reality_config_generation(self):
        """Test REALITY config generation"""
        config = self.reality_profile.to_xray_config()
        
        # Check general structure
        self.assertIn("inbounds", config)
        self.assertIn("outbounds", config)
        self.assertIn("routing", config)
        
        # Check outbound
        proxy_outbound = next(
            (ob for ob in config["outbounds"] if ob["tag"] == "proxy"),
            None
        )
        self.assertIsNotNone(proxy_outbound)
        self.assertEqual(proxy_outbound["protocol"], "vless")
          # Check REALITY settings
        reality_settings = proxy_outbound["streamSettings"]["realitySettings"]
        self.assertEqual(reality_settings["serverName"], "www.example.com")
        self.assertEqual(reality_settings["publicKey"], "test_public_key")

    def test_trojan_config_generation(self):
        """Test Trojan config generation"""
        config = self.trojan_profile.to_xray_config()
        
        proxy_outbound = next(
            (ob for ob in config["outbounds"] if ob["tag"] == "proxy"),
            None
        )
        self.assertIsNotNone(proxy_outbound)
        self.assertEqual(proxy_outbound["protocol"], "trojan")
        
        # Check Trojan settings
        server = proxy_outbound["settings"]["servers"][0]
        self.assertEqual(server["address"], "example.com")
        self.assertEqual(server["password"], "test_password")

class TestHealthChecker(unittest.TestCase):
    """Test HealthChecker class"""
    
    def setUp(self):
        self.health_checker = HealthChecker()
        self.test_profile = ProxyProfile(
            name="test",
            protocol="vless",
            server="127.0.0.1",
            port=443,
            uuid="12345678-1234-1234-1234-123456789012"        )

    @patch('subprocess.Popen')
    @patch('aiohttp.ClientSession.get')
    async def test_proxy_health_check(self, mock_get, mock_popen):
        """Test proxy health check"""
        # Mock Xray process
        mock_process = Mock()
        mock_process.terminate = Mock()
        mock_process.wait = Mock()
        mock_popen.return_value = mock_process
        
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Run test
        success, latency = await self.health_checker.test_proxy(self.test_profile)
        
        # Check results
        self.assertTrue(success)
        self.assertIsInstance(latency, float)
        self.assertGreater(latency, 0)

class TestProfileManager(unittest.TestCase):
    """Test ProfileManager class"""
    
    def setUp(self):
        # Create temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        )
        self.temp_file.close()
        
        self.profile_manager = ProfileManager(self.temp_file.name)

    def tearDown(self):
        # Remove temporary file
        os.unlink(self.temp_file.name)

    def test_profile_creation(self):
        """Test creating default profiles"""
        self.profile_manager.load_profiles()
        
        # Should have at least one profile
        self.assertGreater(len(self.profile_manager.profiles), 0)
        
        # Check first profile type
        first_profile = self.profile_manager.profiles[0]
        self.assertIsInstance(first_profile, ProxyProfile)

    def test_profile_save_load(self):
        """Test saving and loading profiles"""
        # Create test profile
        test_profile = ProxyProfile(
            name="save-test",
            protocol="trojan",
            server="test.example.com",
            port=443,
            password="test123"
        )
        
        self.profile_manager.profiles = [test_profile]
        self.profile_manager.save_profiles()
        
        # Reload
        new_manager = ProfileManager(self.temp_file.name)
        new_manager.load_profiles()
          # Check results
        self.assertEqual(len(new_manager.profiles), 1)
        loaded_profile = new_manager.profiles[0]
        self.assertEqual(loaded_profile.name, "save-test")
        self.assertEqual(loaded_profile.server, "test.example.com")

    def test_best_profile_selection(self):
        """Test best profile selection"""
        # Create test profiles with different stats
        profile1 = ProxyProfile(
            name="slow", protocol="trojan", server="slow.com", port=443,
            password="test", latency=2000, success_rate=0.8, priority=1
        )
        
        profile2 = ProxyProfile(
            name="fast", protocol="trojan", server="fast.com", port=443,
            password="test", latency=100, success_rate=0.9, priority=2
        )
        
        self.profile_manager.profiles = [profile1, profile2]
        
        # Select best
        best = self.profile_manager.get_best_profile()
        
        # First profile should be selected (higher priority)
        self.assertEqual(best.name, "slow")

class TestConfigGenerator(unittest.TestCase):
    """Test ConfigGenerator class"""
    
    def setUp(self):
        self.generator = ConfigGenerator()

    def test_reality_config_generation(self):
        """Test REALITY config generation"""
        config = self.generator.generate_reality_config(
            server_ip="1.2.3.4",
            uuid_str="12345678-1234-1234-1234-123456789012",
            public_key="test_public_key",
            short_id="test_short_id"
        )
        
        # Check structure
        self.assertIn("inbounds", config)
        self.assertIn("outbounds", config)
        
        # Check main outbound
        proxy_outbound = config["outbounds"][0]
        self.assertEqual(proxy_outbound["protocol"], "vless")
        self.assertEqual(proxy_outbound["settings"]["vnext"][0]["address"], "1.2.3.4")

    def test_trojan_config_generation(self):
        """Test Trojan config generation"""
        config = self.generator.generate_trojan_config(
            server_domain="example.com",
            password="test_password"
        )
        
        proxy_outbound = config["outbounds"][0]
        self.assertEqual(proxy_outbound["protocol"], "trojan")
        self.assertEqual(proxy_outbound["settings"]["servers"][0]["address"], "example.com")

    def test_share_url_generation(self):
        """Test subscription URL generation"""
        # Test VLESS URL
        vless_url = self.generator.generate_share_url(
            "vless",
            server="1.2.3.4",
            port=443,
            uuid_str="12345678-1234-1234-1234-123456789012",
            public_key="test_key",
            short_id="test_id"
        )
        
        self.assertTrue(vless_url.startswith("vless://"))
        self.assertIn("1.2.3.4:443", vless_url)
        
        # Test Trojan URL
        trojan_url = self.generator.generate_share_url(
            "trojan",
            server="example.com",
            port=443,
            password="test_password"
        )
        
        self.assertTrue(trojan_url.startswith("trojan://"))
        self.assertIn("example.com:443", trojan_url)

class TestP2PManager(unittest.TestCase):
    """Test P2PManager class"""
    
    def setUp(self):
        self.p2p_manager = P2PManager("wss://test.example.com")

    def test_p2p_manager_initialization(self):
        """Test P2P Manager initialization"""
        self.assertFalse(self.p2p_manager.is_enabled())
        self.assertIsNone(self.p2p_manager.proxy)

    @patch('p2p.webrtc.p2p_fallback.P2PProxy')
    async def test_p2p_enable_disable(self, mock_p2p_proxy):
        """Test P2P enable/disable"""
        # Mock P2PProxy
        mock_proxy = AsyncMock()
        mock_p2p_proxy.return_value = mock_proxy
        
        # Enable
        await self.p2p_manager.enable_fallback(as_helper=False)
        
        # Check enabled
        mock_p2p_proxy.assert_called_once()
        mock_proxy.start_as_client.assert_called_once()
        
        # Disable
        await self.p2p_manager.disable_fallback()
        
        # Check disabled
        mock_proxy.stop.assert_called_once()

class IntegrationTests(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_profiles.yaml")
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def test_full_client_workflow(self):
        """Test complete client workflow"""
        # Create client with temporary file
        client = StealthFlowClient()
        client.profile_manager.config_file = Path(self.config_file)
        
        # Load profiles
        client.profile_manager.load_profiles()
        
        # Check profiles exist
        self.assertGreater(len(client.profile_manager.profiles), 0)
        
        # Test best profile selection
        best_profile = client.profile_manager.get_best_profile()
        
        # If profile exists, it should be selected
        if client.profile_manager.profiles:
            self.assertIsNotNone(best_profile)

def run_performance_tests():
    """Run performance tests"""
    import time
    print("=== Performance Tests ===")
    
    # Test config generation speed
    generator = ConfigGenerator()
    
    start_time = time.time()
    for i in range(100):
        config = generator.generate_reality_config(
            "1.2.3.4", 
            "12345678-1234-1234-1234-123456789012",
            "test_key",
            "test_id"
                )
    end_time = time.time()
    print(f"Config generation: {(end_time - start_time) * 1000:.2f}ms for 100 configs")
    
    # Test URL generation speed
    start_time = time.time()
    for i in range(1000):
        url = generator.generate_share_url(
            "vless",
            server="1.2.3.4",
            port=443,
            uuid_str="12345678-1234-1234-1234-123456789012",
            public_key="test_key",
            short_id="test_id"
        )
    end_time = time.time()
    
    print(f"URL generation: {(end_time - start_time) * 1000:.2f}ms for 1000 URLs")

async def run_async_tests():
    """Run async tests"""
    suite = unittest.TestSuite()
    
    # Add async tests
    suite.addTest(IntegrationTests('test_full_client_workflow'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def main():
    """Main test function"""
    print("StealthFlow Test Suite")
    print("=" * 50)
    
    # Run unit tests
    print("\n1. Running Unit Tests...")
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Run performance tests
    print("\n2. Running Performance Tests...")
    run_performance_tests()
    
    # Run async tests
    print("\n3. Running Async Tests...")
    async_success = asyncio.run(run_async_tests())
    
    # Results summary    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print(f"Unit Tests: {'PASSED' if result.wasSuccessful() else 'FAILED'}")
    print(f"Async Tests: {'PASSED' if async_success else 'FAILED'}")
    
    if result.wasSuccessful() and async_success:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
