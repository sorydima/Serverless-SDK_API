"""
Multicast Discovery Service for Local Node Detection

This module implements local node discovery through UDP multicast
and maintains network topology storage.
"""

import asyncio
import logging
import socket
import struct
import time
import json
import threading
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import ipaddress

logger = logging.getLogger(__name__)


@dataclass
class NodeInfo:
    """Information about a discovered node."""
    node_id: str
    ip_address: str
    port: int
    capabilities: List[str]
    last_seen: float
    node_type: str = "standard"  # standard, bridge, gateway, etc.
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'node_id': self.node_id,
            'ip_address': self.ip_address,
            'port': self.port,
            'capabilities': self.capabilities,
            'last_seen': self.last_seen,
            'node_type': self.node_type,
            'metadata': self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NodeInfo':
        """Create from dictionary."""
        return cls(
            node_id=data['node_id'],
            ip_address=data['ip_address'],
            port=data['port'],
            capabilities=data.get('capabilities', []),
            last_seen=data.get('last_seen', time.time()),
            node_type=data.get('node_type', 'standard'),
            metadata=data.get('metadata', {})
        )

    def is_alive(self, timeout: float = 30.0) -> bool:
        """Check if node is considered alive."""
        return (time.time() - self.last_seen) < timeout


class MulticastDiscoveryMessage:
    """Message format for multicast discovery."""

    MESSAGE_TYPES = {
        'HELLO': 1,      # Node announcement
        'BYE': 2,        # Node departure
        'QUERY': 3,      # Request for node list
        'REPLY': 4,      # Response to query
        'UPDATE': 5,     # Node information update
        'TOPOLOGY': 6    # Network topology information
    }

    def __init__(self, message_type: str, node_info: NodeInfo, sequence_number: int = 0):
        self.message_type = message_type
        self.node_info = node_info
        self.sequence_number = sequence_number
        self.timestamp = time.time()

    def to_bytes(self) -> bytes:
        """Serialize message to bytes."""
        data = {
            'type': self.message_type,
            'sequence': self.sequence_number,
            'timestamp': self.timestamp,
            'node': self.node_info.to_dict()
        }

        json_data = json.dumps(data).encode('utf-8')
        return struct.pack('>I', len(json_data)) + json_data

    @classmethod
    def from_bytes(cls, data: bytes) -> Optional['MulticastDiscoveryMessage']:
        """Deserialize message from bytes."""
        try:
            if len(data) < 4:
                return None

            json_size = struct.unpack('>I', data[:4])[0]
            if len(data) < 4 + json_size:
                return None

            json_data = data[4:4 + json_size]
            parsed = json.loads(json_data.decode('utf-8'))

            node_info = NodeInfo.from_dict(parsed['node'])

            return cls(
                message_type=parsed['type'],
                node_info=node_info,
                sequence_number=parsed.get('sequence', 0)
            )

        except (json.JSONDecodeError, KeyError, struct.error, UnicodeDecodeError):
            return None


class TopologyManager:
    """Manages network topology information."""

    def __init__(self):
        self.topology: Dict[str, List[str]] = {}  # node_id -> list of connected nodes
        self.node_locations: Dict[str, Dict[str, Any]] = {}  # node_id -> location data
        self.topology_lock = threading.Lock()

    def update_connection(self, node1: str, node2: str, connected: bool = True):
        """Update connection between two nodes."""
        with self.topology_lock:
            if connected:
                if node1 not in self.topology:
                    self.topology[node1] = []
                if node2 not in self.topology[node1]:
                    self.topology[node1].append(node2)

                if node2 not in self.topology:
                    self.topology[node2] = []
                if node1 not in self.topology[node2]:
                    self.topology[node2].append(node1)
            else:
                if node1 in self.topology and node2 in self.topology[node1]:
                    self.topology[node1].remove(node2)
                if node2 in self.topology and node1 in self.topology[node2]:
                    self.topology[node2].remove(node1)

    def update_node_location(self, node_id: str, location: Dict[str, Any]):
        """Update location information for a node."""
        with self.topology_lock:
            self.node_locations[node_id] = {
                **location,
                'last_updated': time.time()
            }

    def get_topology(self) -> Dict[str, List[str]]:
        """Get current topology."""
        with self.topology_lock:
            return self.topology.copy()

    def get_node_location(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get location information for a node."""
        with self.topology_lock:
            return self.node_locations.get(node_id)

    def find_shortest_path(self, start_node: str, end_node: str) -> Optional[List[str]]:
        """Find shortest path between two nodes using BFS."""
        if start_node not in self.topology or end_node not in self.topology:
            return None

        with self.topology_lock:
            visited = set()
            queue = [(start_node, [start_node])]

            while queue:
                current, path = queue.pop(0)

                if current == end_node:
                    return path

                if current not in visited:
                    visited.add(current)
                    for neighbor in self.topology[current]:
                        if neighbor not in visited:
                            queue.append((neighbor, path + [neighbor]))

            return None

    def get_network_stats(self) -> Dict[str, Any]:
        """Get topology statistics."""
        with self.topology_lock:
            total_connections = sum(len(connections) for connections in self.topology.values()) // 2
            isolated_nodes = [node for node, connections in self.topology.items() if not connections]

            return {
                'total_nodes': len(self.topology),
                'total_connections': total_connections,
                'isolated_nodes': len(isolated_nodes),
                'average_connections': total_connections * 2 / max(len(self.topology), 1)
            }


class MulticastDiscoveryService:
    """
    UDP Multicast Discovery Service for local node detection.

    Handles node discovery, announcement, and topology management.
    """

    MULTICAST_GROUP = "224.0.0.251"  # IPv4 multicast address
    DISCOVERY_PORT = 5353  # Standard multicast port
    BUFFER_SIZE = 4096

    def __init__(self, node_id: str, node_type: str = "standard"):
        self.node_id = node_id
        self.node_type = node_type
        self.node_info = NodeInfo(
            node_id=node_id,
            ip_address=self._get_local_ip(),
            port=DISCOVERY_PORT,
            capabilities=["mesh", "routing", "discovery"],
            last_seen=time.time(),
            node_type=node_type
        )

        self.discovered_nodes: Dict[str, NodeInfo] = {}
        self.topology_manager = TopologyManager()
        self.message_handlers: Dict[str, Callable] = {}
        self.sequence_number = 0

        # Socket for multicast communication
        self.sock: Optional[socket.socket] = None
        self.running = False
        self.receive_task: Optional[asyncio.Task] = None
        self.announce_task: Optional[asyncio.Task] = None

        # Thread pool for socket operations
        self.executor = ThreadPoolExecutor(max_workers=2)

    def _get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            # Create a socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    def register_message_handler(self, message_type: str, handler: Callable):
        """Register handler for specific message types."""
        self.message_handlers[message_type] = handler

    async def start(self):
        """Start the discovery service."""
        try:
            # Create UDP socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind to port
            self.sock.bind(('', self.DISCOVERY_PORT))

            # Join multicast group
            group = socket.inet_aton(self.MULTICAST_GROUP)
            mreq = struct.pack('4sL', group, socket.INADDR_ANY)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            # Set non-blocking
            self.sock.setblocking(False)

            self.running = True

            # Start background tasks
            self.receive_task = asyncio.create_task(self._receive_messages())
            self.announce_task = asyncio.create_task(self._periodic_announce())

            logger.info(f"Multicast discovery service started for node {self.node_id}")

        except Exception as e:
            logger.error(f"Failed to start discovery service: {e}")
            self.running = False

    async def stop(self):
        """Stop the discovery service."""
        self.running = False

        if self.announce_task:
            self.announce_task.cancel()
            try:
                await self.announce_task
            except asyncio.CancelledError:
                pass

        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass

        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass

        # Send bye message
        await self._send_bye_message()

        logger.info(f"Multicast discovery service stopped for node {self.node_id}")

    async def _receive_messages(self):
        """Receive and process multicast messages."""
        while self.running:
            try:
                # Receive message
                data, addr = await asyncio.get_event_loop().run_in_executor(
                    self.executor, self._recvfrom_blocking
                )

                if data:
                    message = MulticastDiscoveryMessage.from_bytes(data)
                    if message:
                        await self._process_message(message, addr)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"Error receiving message: {e}")
                await asyncio.sleep(0.1)

    def _recvfrom_blocking(self) -> Optional[Tuple[bytes, tuple]]:
        """Blocking receive for socket."""
        if self.sock:
            try:
                return self.sock.recvfrom(self.BUFFER_SIZE)
            except socket.error:
                return None
        return None

    async def _process_message(self, message: MulticastDiscoveryMessage, addr: tuple):
        """Process received discovery message."""
        try:
            sender_ip = addr[0]

            # Update node info with sender address
            message.node_info.ip_address = sender_ip
            message.node_info.last_seen = time.time()

            # Skip our own messages
            if message.node_info.node_id == self.node_id:
                return

            # Process based on message type
            if message.message_type == "HELLO":
                await self._handle_hello(message.node_info)
            elif message.message_type == "BYE":
                await self._handle_bye(message.node_info)
            elif message.message_type == "QUERY":
                await self._handle_query(message.node_info)
            elif message.message_type == "UPDATE":
                await self._handle_update(message.node_info)
            elif message.message_type == "TOPOLOGY":
                await self._handle_topology(message.node_info)

            # Call custom handlers
            if message.message_type in self.message_handlers:
                await self.message_handlers[message.message_type](message.node_info)

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _handle_hello(self, node_info: NodeInfo):
        """Handle node hello message."""
        self.discovered_nodes[node_info.node_id] = node_info
        logger.info(f"Discovered node: {node_info.node_id} at {node_info.ip_address}")

        # Update topology
        self.topology_manager.update_connection(self.node_id, node_info.node_id)

    async def _handle_bye(self, node_info: NodeInfo):
        """Handle node bye message."""
        if node_info.node_id in self.discovered_nodes:
            del self.discovered_nodes[node_info.node_id]
            logger.info(f"Node departed: {node_info.node_id}")

            # Update topology
            self.topology_manager.update_connection(self.node_id, node_info.node_id, False)

    async def _handle_query(self, node_info: NodeInfo):
        """Handle node query message."""
        # Send reply with our node list
        await self._send_reply(node_info)

    async def _handle_update(self, node_info: NodeInfo):
        """Handle node update message."""
        self.discovered_nodes[node_info.node_id] = node_info
        logger.debug(f"Updated node info: {node_info.node_id}")

    async def _handle_topology(self, node_info: NodeInfo):
        """Handle topology information."""
        # Update our topology knowledge
        if node_info.metadata and 'topology' in node_info.metadata:
            remote_topology = node_info.metadata['topology']
            for node, connections in remote_topology.items():
                for connected_node in connections:
                    self.topology_manager.update_connection(node, connected_node)

    async def _send_reply(self, requester: NodeInfo):
        """Send reply to query."""
        reply_info = NodeInfo(
            node_id=self.node_id,
            ip_address=self.node_info.ip_address,
            port=self.DISCOVERY_PORT,
            capabilities=self.node_info.capabilities,
            last_seen=time.time(),
            node_type=self.node_type,
            metadata={
                'known_nodes': [node.to_dict() for node in self.discovered_nodes.values()]
            }
        )

        message = MulticastDiscoveryMessage("REPLY", reply_info, self.sequence_number)
        await self._send_message(message)

    async def _periodic_announce(self):
        """Periodically announce our presence."""
        while self.running:
            try:
                await self._send_hello_message()
                await asyncio.sleep(30.0)  # Announce every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic announce: {e}")
                await asyncio.sleep(30.0)

    async def _send_hello_message(self):
        """Send hello message to announce presence."""
        message = MulticastDiscoveryMessage("HELLO", self.node_info, self.sequence_number)
        await self._send_message(message)
        self.sequence_number += 1

    async def _send_bye_message(self):
        """Send bye message when leaving."""
        message = MulticastDiscoveryMessage("BYE", self.node_info, self.sequence_number)
        await self._send_message(message)
        self.sequence_number += 1

    async def _send_message(self, message: MulticastDiscoveryMessage):
        """Send message via multicast."""
        if not self.sock:
            return

        try:
            data = message.to_bytes()
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.sock.sendto(data, (self.MULTICAST_GROUP, self.DISCOVERY_PORT))
            )
        except Exception as e:
            logger.error(f"Failed to send multicast message: {e}")

    async def query_network(self) -> List[NodeInfo]:
        """Query network for all known nodes."""
        # Send query message
        query_info = NodeInfo(
            node_id=self.node_id,
            ip_address=self.node_info.ip_address,
            port=self.DISCOVERY_PORT,
            capabilities=self.node_info.capabilities,
            last_seen=time.time(),
            node_type=self.node_type
        )

        message = MulticastDiscoveryMessage("QUERY", query_info, self.sequence_number)
        await self._send_message(message)
        self.sequence_number += 1

        # Wait a bit for replies
        await asyncio.sleep(2.0)

        return list(self.discovered_nodes.values())

    def get_discovered_nodes(self) -> List[NodeInfo]:
        """Get list of discovered nodes."""
        return list(self.discovered_nodes.values())

    def get_alive_nodes(self, timeout: float = 60.0) -> List[NodeInfo]:
        """Get list of alive nodes."""
        current_time = time.time()
        return [
            node for node in self.discovered_nodes.values()
            if (current_time - node.last_seen) < timeout
        ]

    def get_topology(self) -> Dict[str, List[str]]:
        """Get current network topology."""
        return self.topology_manager.get_topology()

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics."""
        topology_stats = self.topology_manager.get_network_stats()

        return {
            'node_id': self.node_id,
            'discovered_nodes': len(self.discovered_nodes),
            'alive_nodes': len(self.get_alive_nodes()),
            'running': self.running,
            **topology_stats
        }


class MulticastDiscoveryNetwork:
    """
    Multicast Discovery Network coordinator.

    Manages multiple discovery services and network-wide discovery.
    """

    def __init__(self):
        self.services: Dict[str, MulticastDiscoveryService] = {}
        self.global_topology: Dict[str, List[str]] = {}

    def add_service(self, node_id: str, node_type: str = "standard") -> MulticastDiscoveryService:
        """Add a discovery service for a node."""
        if node_id not in self.services:
            self.services[node_id] = MulticastDiscoveryService(node_id, node_type)
        return self.services[node_id]

    async def start_all_services(self):
        """Start all discovery services."""
        tasks = [service.start() for service in self.services.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def stop_all_services(self):
        """Stop all discovery services."""
        tasks = [service.stop() for service in self.services.values()]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_topology_update(self):
        """Broadcast topology information across network."""
        for service in self.services.values():
            topology = service.get_topology()

            # Create topology message
            topology_info = NodeInfo(
                node_id=service.node_id,
                ip_address=service.node_info.ip_address,
                port=service.DISCOVERY_PORT,
                capabilities=service.node_info.capabilities,
                last_seen=time.time(),
                node_type=service.node_type,
                metadata={'topology': topology}
            )

            message = MulticastDiscoveryMessage("TOPOLOGY", topology_info, service.sequence_number)
            await service._send_message(message)
            service.sequence_number += 1

    def get_global_topology(self) -> Dict[str, List[str]]:
        """Get combined topology from all services."""
        combined = {}
        for service in self.services.values():
            topology = service.get_topology()
            for node, connections in topology.items():
                if node not in combined:
                    combined[node] = []
                for conn in connections:
                    if conn not in combined[node]:
                        combined[node].append(conn)
        return combined

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network-wide statistics."""
        service_stats = [service.get_network_stats() for service in self.services.values()]

        total_discovered = sum(stats['discovered_nodes'] for stats in service_stats)
        total_alive = sum(stats['alive_nodes'] for stats in service_stats)

        return {
            'total_services': len(self.services),
            'total_discovered_nodes': total_discovered,
            'total_alive_nodes': total_alive,
            'global_topology': self.get_global_topology(),
            'service_stats': service_stats
        }
