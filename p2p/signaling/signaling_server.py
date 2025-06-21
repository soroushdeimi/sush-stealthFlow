#!/usr/bin/env python3
"""
StealthFlow P2P Signaling Server
Secure signaling server for establishing WebRTC connections between peers
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Set
import websockets
from websockets.server import WebSocketServerProtocol
from pathlib import Path
import sys

# Add utils to path for security module
sys.path.append(str(Path(__file__).parent.parent.parent / "utils"))
from security import SecurityContext, InputValidator, RateLimiter, sanitize_log_message

logger = logging.getLogger('StealthFlow.Signaling')

class Peer:
    """Class representing a peer connection with security features"""
    
    def __init__(self, peer_id: str, websocket: WebSocketServerProtocol, remote_address: str):
        self.peer_id = peer_id
        self.websocket = websocket
        self.remote_address = remote_address
        self.is_helper = False
        self.country = ""
        self.bandwidth = 0
        self.connected_time = time.time()
        self.last_activity = time.time()
        self.message_count = 0
        self.is_authenticated = False
        self.reputation_score = 50  # Start with neutral reputation
        
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()
        self.message_count += 1
    
    def is_active(self, timeout_seconds: int = 300) -> bool:
        """Check if peer is still active"""
        return time.time() - self.last_activity < timeout_seconds
    
    def update_reputation(self, delta: int):
        """Update peer reputation score"""
        self.reputation_score = max(0, min(100, self.reputation_score + delta))
    
    def is_trusted(self) -> bool:
        """Check if peer is trusted based on reputation"""
        return self.reputation_score >= 60 and self.is_authenticated

class SignalingServer:
    """Secure WebRTC signaling server for peer connections"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.peers: Dict[str, Peer] = {}
        self.helpers: Set[str] = set()
        self.clients: Set[str] = set()
        self.running = False
        self.start_time = time.time()
        
        # Security components
        self.security_context = SecurityContext()
        self.rate_limiter = RateLimiter(max_requests=50, window_seconds=60)
        self.connection_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "rejected_connections": 0,
            "security_violations": 0
        }

    async def start(self):
        """Start the signaling server with security checks"""
        self.running = True
        logger.info(f"Starting secure signaling server on {self.host}:{self.port}")
        
        async with websockets.serve(
            self.handle_connection,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10,
            max_size=8192,  # Limit message size
            max_queue=32    # Limit connection queue
        ):
            logger.info("Secure signaling server started successfully")
            await asyncio.Future()  # Run forever

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str):
        """Handle new WebSocket connection with security checks"""
        remote_address = websocket.remote_address[0] if websocket.remote_address else "unknown"
        
        # Rate limiting for new connections
        if not self.connection_rate_limiter.is_allowed(remote_address):
            logger.warning(f"Connection rate limit exceeded for {remote_address}")
            self.stats["rejected_connections"] += 1
            await websocket.close(code=1008, reason="Rate limit exceeded")
            return
        
        peer_id = str(uuid.uuid4())
        peer = Peer(peer_id, websocket, remote_address)
        self.peers[peer_id] = peer
        self.stats["total_connections"] += 1
        
        logger.info(sanitize_log_message(f"New peer connected: {peer_id} from {remote_address}"))
        
        try:
            # Send welcome message
            await self.send_to_peer(peer_id, {
                "type": "welcome",
                "peer_id": peer_id,
                "server_time": time.time(),
                "max_message_size": 8192
            })
            
            # Handle messages
            async for message in websocket:
                try:
                    # Rate limiting per peer
                    if not self.rate_limiter.is_allowed(peer_id):
                        logger.warning(f"Message rate limit exceeded for peer {peer_id}")
                        peer.update_reputation(-10)
                        break
                    
                    # Parse and validate message
                    data = json.loads(message)
                    
                    # Security validation
                    if not self.validate_message(peer, data):
                        logger.warning(f"Invalid message from peer {peer_id}")
                        peer.update_reputation(-5)
                        self.stats["security_violations"] += 1
                        continue
                    
                    await self.handle_message(peer, data)
                    peer.update_activity()
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {peer_id}")
                    peer.update_reputation(-2)
                except Exception as e:
                    logger.error(f"Error handling message from {peer_id}: {e}")
                    peer.update_reputation(-1)
                    
        except websockets.ConnectionClosed:
            logger.info(f"Peer {peer_id} disconnected")
        except Exception as e:
            logger.error(f"Connection error with {peer_id}: {e}")
        finally:
            await self.cleanup_peer(peer_id)

    def validate_message(self, peer: Peer, message: Dict) -> bool:
        """Validate incoming message for security"""
        try:
            # Check message structure
            if not isinstance(message, dict):
                return False
            
            # Check required fields
            if "type" not in message:
                return False
            
            message_type = message["type"]
            
            # Validate message type
            allowed_types = [
                "helper_available", "request_help", "offer", "answer", 
                "ice_candidate", "ping", "auth_request", "auth_response"
            ]
            if message_type not in allowed_types:
                return False
            
            # Validate field lengths and content
            for key, value in message.items():
                if isinstance(value, str):
                    # Limit string lengths
                    if len(value) > 1024:
                        return False
                    
                    # Check for dangerous content
                    if any(char in value for char in ['\0', '\x1a']):
                        return False
            
            # Type-specific validation
            if message_type == "offer" or message_type == "answer":
                if "to" not in message:
                    return False
                if not InputValidator.validate_uuid(message["to"]):
                    return False
            
            # Check authentication for sensitive operations
            if message_type in ["helper_available", "offer", "answer"]:
                if not peer.is_authenticated and message_type != "auth_request":
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Message validation error: {e}")
            return False

    async def authenticate_peer(self, peer: Peer, auth_data: Dict) -> bool:
        """Authenticate peer connection"""
        try:
            # Simple challenge-response authentication
            challenge = auth_data.get("challenge")
            response = auth_data.get("response")
            
            if not challenge or not response:
                return False
            
            # In a real implementation, you would verify the response
            # For now, we'll use a simple check
            expected_response = f"stealthflow-{challenge}-verified"
            
            if response == expected_response:
                peer.is_authenticated = True
                peer.update_reputation(10)
                logger.info(f"Peer {peer.peer_id} authenticated successfully")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Authentication error for peer {peer.peer_id}: {e}")
            return False

    async def handle_message(self, peer: Peer, message: Dict):
        """Handle incoming message from peer with security checks"""
        message_type = message.get("type")
        
        # Handle authentication first
        if message_type == "auth_request":
            auth_challenge = f"challenge-{int(time.time())}-{peer.peer_id[:8]}"
            await self.send_to_peer(peer.peer_id, {
                "type": "auth_challenge",
                "challenge": auth_challenge
            })
            return
        
        if message_type == "auth_response":
            success = await self.authenticate_peer(peer, message)
            await self.send_to_peer(peer.peer_id, {
                "type": "auth_result",
                "success": success
            })
            return
        
        # Require authentication for most operations
        if not peer.is_authenticated and message_type not in ["ping"]:
            await self.send_to_peer(peer.peer_id, {
                "type": "auth_required",
                "message": "Authentication required for this operation"
            })
            return
        
        # Process authenticated messages
        if message_type == "helper_available":
            await self.handle_helper_available(peer, message)
        elif message_type == "request_help":
            await self.handle_request_help(peer, message)
        elif message_type == "offer":
            await self.handle_offer(peer, message)
        elif message_type == "answer":
            await self.handle_answer(peer, message)
        elif message_type == "ice_candidate":
            await self.handle_ice_candidate(peer, message)
        elif message_type == "ping":
            await self.handle_ping(peer)
        else:
            logger.warning(f"Unknown message type: {message_type}")
            peer.update_reputation(-1)

    async def handle_helper_available(self, peer: Peer, message: Dict):
        """Process helper availability announcement with validation"""
        # Validate helper capabilities
        country = message.get("country", "")
        bandwidth = message.get("bandwidth", 0)
        
        # Input validation
        if country and not InputValidator.validate_server_address(country, allow_ip=False):
            if len(country) > 2 or not country.isalpha():
                logger.warning(f"Invalid country from peer {peer.peer_id}")
                return
        
        if not isinstance(bandwidth, (int, float)) or bandwidth < 0 or bandwidth > 10000:
            bandwidth = 0
        
        peer.is_helper = True
        peer.country = InputValidator.sanitize_string(country, max_length=2)
        peer.bandwidth = min(bandwidth, 10000)  # Cap bandwidth value
        
        self.helpers.add(peer.peer_id)
        self.clients.discard(peer.peer_id)
        
        logger.info(sanitize_log_message(f"Helper {peer.peer_id} available from {peer.country}"))
        
        await self.send_to_peer(peer.peer_id, {
            "type": "helper_registered",
            "helper_count": len(self.helpers)
        })

    async def handle_request_help(self, peer: Peer, message: Dict):
        """Process help request with security checks"""
        country = message.get("country", "")
        
        # Validate country input
        if country and len(country) > 2:
            country = country[:2]
        
        peer.country = InputValidator.sanitize_string(country, max_length=2)
        
        self.clients.add(peer.peer_id)
        self.helpers.discard(peer.peer_id)
        
        logger.info(sanitize_log_message(f"Client {peer.peer_id} requesting help from {peer.country}"))
        
        best_helper = await self.find_best_helper(peer)
        
        if best_helper:
            # Only connect trusted peers
            if not best_helper.is_trusted():
                logger.warning(f"Helper {best_helper.peer_id} not trusted, skipping")
                await self.send_to_peer(peer.peer_id, {
                    "type": "no_helper_available",
                    "message": "No trusted helpers currently available"
                })
                return
            
            await self.send_to_peer(best_helper.peer_id, {
                "type": "helper_request",
                "from": peer.peer_id,
                "client_country": peer.country
            })
            
            await self.send_to_peer(peer.peer_id, {
                "type": "helper_found",
                "helper_id": best_helper.peer_id,
                "helper_country": best_helper.country
            })
        else:
            await self.send_to_peer(peer.peer_id, {
                "type": "no_helper_available",
                "message": "No helpers currently available"
            })

    async def handle_offer(self, peer: Peer, message: Dict):
        """Handle WebRTC offer with validation"""
        target_id = message.get("to")
        offer = message.get("offer")
        
        # Validate target peer ID
        if not target_id or not InputValidator.validate_uuid(target_id):
            logger.warning(f"Invalid target ID in offer from {peer.peer_id}")
            return
        
        if target_id not in self.peers:
            logger.warning(f"Target peer {target_id} not found for offer from {peer.peer_id}")
            return
        
        target_peer = self.peers[target_id]
        
        # Only allow offers between trusted peers
        if not peer.is_trusted() or not target_peer.is_trusted():
            logger.warning(f"Untrusted peers attempting connection: {peer.peer_id} -> {target_id}")
            return
        
        await self.send_to_peer(target_id, {
            "type": "offer",
            "from": peer.peer_id,
            "offer": offer
        })

    async def handle_answer(self, peer: Peer, message: Dict):
        """Handle WebRTC answer with validation"""
        target_id = message.get("to")
        answer = message.get("answer")
        
        # Validate target peer ID
        if not target_id or not InputValidator.validate_uuid(target_id):
            logger.warning(f"Invalid target ID in answer from {peer.peer_id}")
            return
        
        if target_id not in self.peers:
            logger.warning(f"Target peer {target_id} not found for answer from {peer.peer_id}")
            return
        
        target_peer = self.peers[target_id]
        
        # Only allow answers between trusted peers
        if not peer.is_trusted() or not target_peer.is_trusted():
            logger.warning(f"Untrusted peers attempting connection: {peer.peer_id} -> {target_id}")
            return
        
        await self.send_to_peer(target_id, {
            "type": "answer",
            "from": peer.peer_id,
            "answer": answer
        })

    async def handle_ice_candidate(self, peer: Peer, message: Dict):
        """Handle ICE candidate with validation"""
        target_id = message.get("to")
        candidate = message.get("candidate")
        
        # Validate target peer ID
        if not target_id or not InputValidator.validate_uuid(target_id):
            logger.warning(f"Invalid target ID in ICE candidate from {peer.peer_id}")
            return
        
        if target_id not in self.peers:
            return
        
        target_peer = self.peers[target_id]
        
        # Only allow ICE candidates between trusted peers
        if not peer.is_trusted() or not target_peer.is_trusted():
            return
        
        await self.send_to_peer(target_id, {
            "type": "ice_candidate",
            "from": peer.peer_id,
            "candidate": candidate
        })

    async def handle_ping(self, peer: Peer):
        """Handle ping message"""
        await self.send_to_peer(peer.peer_id, {
            "type": "pong",
            "timestamp": time.time()
        })

    async def find_best_helper(self, client_peer: Peer):
        """Find the best available helper for client with trust checks"""
        available_helpers = []
        
        for helper_id in self.helpers:
            if helper_id in self.peers:
                helper = self.peers[helper_id]
                
                # Only consider trusted helpers
                if not helper.is_trusted():
                    continue
                
                # Prefer helpers from different countries
                if helper.country != client_peer.country:
                    available_helpers.append(helper)
        
        # If no foreign helpers, use any trusted helper
        if not available_helpers:
            for helper_id in self.helpers:
                if helper_id in self.peers:
                    helper = self.peers[helper_id]
                    if helper.is_trusted():
                        available_helpers.append(helper)
        
        if available_helpers:
            # Sort by reputation, then bandwidth, then connection time
            available_helpers.sort(
                key=lambda h: (-h.reputation_score, -h.bandwidth, h.connected_time)
            )
            return available_helpers[0]
        
        return None

    async def send_to_peer(self, peer_id: str, message: Dict):
        """Send message to specific peer with error handling"""
        if peer_id in self.peers:
            try:
                # Sanitize message before sending
                sanitized_message = {}
                for key, value in message.items():
                    if isinstance(value, str):
                        sanitized_message[key] = InputValidator.sanitize_string(value, max_length=1024)
                    else:
                        sanitized_message[key] = value
                
                await self.peers[peer_id].websocket.send(json.dumps(sanitized_message))
            except websockets.ConnectionClosed:
                await self.cleanup_peer(peer_id)
            except Exception as e:
                logger.error(f"Failed to send to {peer_id}: {e}")

    async def cleanup_peer(self, peer_id: str):
        """Clean up peer data when disconnected"""
        if peer_id in self.peers:
            self.helpers.discard(peer_id)
            self.clients.discard(peer_id)
            del self.peers[peer_id]
            logger.info(sanitize_log_message(f"Cleaned up peer {peer_id}"))

    def get_stats(self) -> Dict:
        """Get server statistics"""
        return {
            "total_peers": len(self.peers),
            "helpers": len(self.helpers),
            "clients": len(self.clients),
            "uptime": time.time() - self.start_time,
            "stats": self.stats
        }

async def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = SignalingServer()
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down signaling server...")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
