"""
Wi-Fi Direct Mesh Networking for Peer-to-Peer Communication

This module implements peer-to-peer packet exchange through Wi-Fi Direct
between devices without internet connectivity.
"""

import asyncio
import logging
import socket
import struct
import time
import threading
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import json

logger = logging.getLogger(__name__)


@dataclass
class WiFiDirectMessage:
    """Represents a message in the Wi-Fi Direct mesh network."""
    message_id: str
    source_id: str
    destination_id: str
    payload: bytes
    timestamp: float
    message_type: str = "data"
    priority: int = 1  # 1=low, 2=normal, 3=high
    ttl: int = 32

    def to_bytes(self) -> bytes:
        """Serialize message to bytes for transmission."""
        header = {
            'message_id': self.message_id,
            'source_id': self.source_id,
            'destination_id': self.destination_id,
            'timestamp': self.timestamp,
            'message_type': self.message_type,
            'priority': self.priority,
            'ttl': self.ttl,
            'payload_size': len(self.payload)
        }

        header_json = json.dumps(header).encode('utf-8')
        header_size = struct.pack('>I', len(header_json))

        return header_size + header_json + self.payload

    @classmethod
    def from_bytes(cls, data: bytes) -> Optional['WiFiDirectMessage']:
        """Deserialize message from bytes."""
        try:
            if len(data) < 4:
                return None

            header_size = struct.unpack('>I', data[:4])[0]
            if len(data) < 4 + header_size:
                return None

            header_json = data[4:4 + header_size]
            header = json.loads(header_json.decode('utf-8'))

            payload_start = 4 + header_size
            payload_size = header.get('payload_size', 0)
            if len(data) < payload_start + payload_size:
                return None

            payload = data[payload_start:payload_start + payload_size]

            return cls(
                message_id=header['message_id'],
                source_id=header['source_id'],
                destination_id=header['destination_id'],
                payload=payload,
                timestamp=header['timestamp'],
                message_type=header.get('message_type', 'data'),
                priority=header.get('priority', 1),
                ttl=header.get('ttl', 32)
            )
        except (json.JSONDecodeError, KeyError, struct.error, UnicodeDecodeError):
            return None


class WiFiDirectConnection:
    """Manages Wi-Fi Direct connection to a peer."""

    def __init__(self, peer_address: Tuple[str, int], device_id: str):
        self.peer_address = peer_address
        self.device_id = device_id
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.last_seen = time.time()
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.receive_task: Optional[asyncio.Task] = None

    async def connect(self) -> bool:
        """Establish Wi-Fi Direct connection to peer."""
        try:
            # Simulate Wi-Fi Direct connection (in real implementation, use wifi-direct libraries)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)

            # In real implementation, this would use Wi-Fi Direct APIs
            # For simulation, assume connection succeeds
            self.connected = True
            self.last_seen = time.time()

            # Start receiving messages
            self.receive_task = asyncio.create_task(self._receive_messages())

            logger.info(f"Connected to peer at {self.peer_address}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to peer {self.peer_address}: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from peer."""
        self.connected = False

        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass

        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None

        logger.info(f"Disconnected from peer at {self.peer_address}")

    async def send_message(self, message: WiFiDirectMessage) -> bool:
        """Send message to peer."""
        if not self.connected or not self.socket:
            return False

        try:
            data = message.to_bytes()
            # Simulate sending (in real implementation, use socket.sendall)
            await asyncio.sleep(0.01)  # Simulate network delay
            logger.debug(f"Sent message {message.message_id} to {self.peer_address}")
            return True

        except Exception as e:
            logger.error(f"Failed to send message to {self.peer_address}: {e}")
            self.connected = False
            return False

    async def _receive_messages(self):
        """Receive messages from peer."""
        while self.connected:
            try:
                # Simulate receiving messages (in real implementation, use socket.recv)
                await asyncio.sleep(1.0)  # Check for messages periodically

                # Simulate receiving a message occasionally
                if asyncio.get_event_loop().time() % 10 < 1:  # 10% chance per second
                    # This would be actual message reception in real implementation
                    pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error receiving messages from {self.peer_address}: {e}")
                self.connected = False
                break

    def is_alive(self) -> bool:
        """Check if connection is alive."""
        return self.connected and (time.time() - self.last_seen) < 30.0


class WiFiDirectGroup:
    """Manages a Wi-Fi Direct group of connected peers."""

    def __init__(self, group_owner_id: str):
        self.group_owner_id = group_owner_id
        self.peers: Dict[str, WiFiDirectConnection] = {}
        self.group_info = {
            'ssid': f"WiFiDirect_{group_owner_id}",
            'passphrase': self._generate_passphrase(),
            'frequency': 2412,  # Channel 1
            'max_peers': 8
        }

    def _generate_passphrase(self) -> str:
        """Generate WPA2 passphrase for group."""
        # In real implementation, use secure random generation
        return "SecurePass123"

    def add_peer(self, peer_id: str, peer_address: Tuple[str, int]) -> WiFiDirectConnection:
        """Add peer to the group."""
        if peer_id not in self.peers and len(self.peers) < self.group_info['max_peers']:
            self.peers[peer_id] = WiFiDirectConnection(peer_address, peer_id)
        return self.peers[peer_id]

    def remove_peer(self, peer_id: str):
        """Remove peer from the group."""
        if peer_id in self.peers:
            asyncio.create_task(self.peers[peer_id].disconnect())
            del self.peers[peer_id]

    async def broadcast_to_group(self, message: WiFiDirectMessage, exclude_peer: Optional[str] = None):
        """Broadcast message to all peers in group."""
        tasks = []
        for peer_id, connection in self.peers.items():
            if peer_id != exclude_peer and connection.is_alive():
                tasks.append(connection.send_message(message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_group_info(self) -> Dict[str, Any]:
        """Get group information."""
        return {
            **self.group_info,
            'connected_peers': len([p for p in self.peers.values() if p.is_alive()]),
            'total_peers': len(self.peers)
        }


class WiFiDirectMeshNode:
    """
    Wi-Fi Direct Mesh Node for peer-to-peer communication.

    Handles group formation, peer discovery, and message routing.
    """

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.groups: Dict[str, WiFiDirectGroup] = {}
        self.active_connections: Dict[str, WiFiDirectConnection] = {}
        self.routing_table: Dict[str, str] = {}  # destination -> next_hop
        self.message_handlers: Dict[str, Callable] = {}
        self.message_cache: Dict[str, float] = {}  # message_id -> timestamp
        self.discovery_active = False

        # Thread pool for blocking operations
        self.executor = ThreadPoolExecutor(max_workers=4)

    def register_message_handler(self, message_type: str, handler: Callable):
        """Register handler for specific message types."""
        self.message_handlers[message_type] = handler

    async def start_group(self, group_id: str) -> WiFiDirectGroup:
        """Start a new Wi-Fi Direct group as group owner."""
        if group_id not in self.groups:
            self.groups[group_id] = WiFiDirectGroup(self.device_id)
            logger.info(f"Started Wi-Fi Direct group: {group_id}")
        return self.groups[group_id]

    async def join_group(self, group_id: str, group_info: Dict[str, Any]) -> bool:
        """Join an existing Wi-Fi Direct group."""
        try:
            # Simulate joining group (in real implementation, use Wi-Fi Direct APIs)
            group_owner_address = ("192.168.49.1", 8080)  # Default group owner IP

            connection = WiFiDirectConnection(group_owner_address, self.device_id)
            success = await connection.connect()

            if success:
                self.active_connections[group_id] = connection
                self.groups[group_id] = WiFiDirectGroup(group_info.get('owner_id', 'unknown'))
                logger.info(f"Joined Wi-Fi Direct group: {group_id}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to join group {group_id}: {e}")
            return False

    async def discover_groups(self) -> List[Dict[str, Any]]:
        """Discover available Wi-Fi Direct groups."""
        try:
            # Simulate group discovery (in real implementation, scan for Wi-Fi Direct groups)
            discovered_groups = [
                {
                    'group_id': 'group_001',
                    'owner_id': 'device_001',
                    'ssid': 'WiFiDirect_device_001',
                    'signal_strength': -45
                },
                {
                    'group_id': 'group_002',
                    'owner_id': 'device_002',
                    'ssid': 'WiFiDirect_device_002',
                    'signal_strength': -52
                }
            ]

            logger.info(f"Discovered {len(discovered_groups)} Wi-Fi Direct groups")
            return discovered_groups

        except Exception as e:
            logger.error(f"Failed to discover groups: {e}")
            return []

    async def send_message(self, destination_id: str, message_type: str, payload: bytes) -> bool:
        """Send message to destination through Wi-Fi Direct mesh."""
        try:
            message = WiFiDirectMessage(
                message_id=f"{self.device_id}_{int(time.time() * 1000)}",
                source_id=self.device_id,
                destination_id=destination_id,
                payload=payload,
                timestamp=time.time(),
                message_type=message_type
            )

            # Check if destination is directly connected
            if destination_id in self.active_connections:
                return await self.active_connections[destination_id].send_message(message)

            # Otherwise, broadcast to all groups
            for group in self.groups.values():
                await group.broadcast_to_group(message)

            logger.info(f"Sent message {message.message_id} to {destination_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def broadcast_message(self, message_type: str, payload: bytes):
        """Broadcast message to all connected peers."""
        try:
            message = WiFiDirectMessage(
                message_id=f"{self.device_id}_broadcast_{int(time.time() * 1000)}",
                source_id=self.device_id,
                destination_id="broadcast",
                payload=payload,
                timestamp=time.time(),
                message_type=message_type
            )

            for group in self.groups.values():
                await group.broadcast_to_group(message)

            logger.info(f"Broadcasted message of type {message_type}")

        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")

    async def maintain_connections(self):
        """Maintain active connections and clean up dead ones."""
        while True:
            try:
                # Check connection health
                dead_connections = []
                for group_id, connection in self.active_connections.items():
                    if not connection.is_alive():
                        dead_connections.append(group_id)

                # Clean up dead connections
                for group_id in dead_connections:
                    logger.warning(f"Connection to group {group_id} lost")
                    await self.active_connections[group_id].disconnect()
                    del self.active_connections[group_id]

                # Clean old message cache
                current_time = time.time()
                expired_messages = [
                    msg_id for msg_id, timestamp in self.message_cache.items()
                    if current_time - timestamp > 300  # 5 minutes
                ]
                for msg_id in expired_messages:
                    del self.message_cache[msg_id]

                await asyncio.sleep(10.0)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error maintaining connections: {e}")
                await asyncio.sleep(10.0)

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics."""
        total_peers = sum(len(group.peers) for group in self.groups.values())
        active_connections = len([c for c in self.active_connections.values() if c.is_alive()])

        return {
            'device_id': self.device_id,
            'active_groups': len(self.groups),
            'active_connections': active_connections,
            'total_peers': total_peers,
            'messages_cached': len(self.message_cache)
        }


class WiFiDirectMeshNetwork:
    """
    Wi-Fi Direct Mesh Network coordinator.

    Manages multiple Wi-Fi Direct mesh nodes and network-wide operations.
    """

    def __init__(self):
        self.nodes: Dict[str, WiFiDirectMeshNode] = {}
        self.network_topology: Dict[str, List[str]] = {}

    def add_node(self, device_id: str) -> WiFiDirectMeshNode:
        """Add a new node to the mesh network."""
        if device_id not in self.nodes:
            self.nodes[device_id] = WiFiDirectMeshNode(device_id)
            self.network_topology[device_id] = []
        return self.nodes[device_id]

    async def create_mesh_group(self, group_id: str, owner_id: str) -> bool:
        """Create a new mesh group."""
        if owner_id in self.nodes:
            group = await self.nodes[owner_id].start_group(group_id)
            logger.info(f"Created mesh group {group_id} with owner {owner_id}")
            return True
        return False

    async def connect_nodes(self, node1_id: str, node2_id: str, group_id: str):
        """Connect two nodes through a Wi-Fi Direct group."""
        if node1_id in self.nodes and node2_id in self.nodes:
            # Node 1 creates/joins group
            if group_id not in self.nodes[node1_id].groups:
                await self.nodes[node1_id].start_group(group_id)

            # Node 2 joins group
            group_info = {'owner_id': node1_id}
            await self.nodes[node2_id].join_group(group_id, group_info)

            # Update topology
            if node2_id not in self.network_topology[node1_id]:
                self.network_topology[node1_id].append(node2_id)
            if node1_id not in self.network_topology[node2_id]:
                self.network_topology[node2_id].append(node1_id)

    async def broadcast_network_message(self, source_id: str, message_type: str, payload: bytes):
        """Broadcast message across entire network."""
        if source_id in self.nodes:
            await self.nodes[source_id].broadcast_message(message_type, payload)

    def get_network_topology(self) -> Dict[str, List[str]]:
        """Get current network topology."""
        return self.network_topology.copy()

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network-wide statistics."""
        node_stats = [node.get_network_stats() for node in self.nodes.values()]

        return {
            'total_nodes': len(self.nodes),
            'network_topology': self.get_network_topology(),
            'node_stats': node_stats
        }
