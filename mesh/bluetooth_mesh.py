"""
Bluetooth LE Mesh Networking for Offline Message Transmission

This module implements offline message transmission through Bluetooth LE Advertising
with Mesh API integration and encryption support.
"""

import asyncio
import logging
import struct
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

logger = logging.getLogger(__name__)


@dataclass
class BLEMeshMessage:
    """Represents a message in the Bluetooth mesh network."""
    message_id: str
    source_id: str
    destination_id: str
    payload: bytes
    timestamp: float
    ttl: int = 64  # Time to live
    hop_count: int = 0

    def to_bytes(self) -> bytes:
        """Serialize message to bytes for BLE advertising."""
        data = (
            self.message_id.encode('utf-8') +
            b'\x00' +
            self.source_id.encode('utf-8') +
            b'\x00' +
            self.destination_id.encode('utf-8') +
            b'\x00' +
            self.payload +
            struct.pack('>dI', self.timestamp, self.ttl)
        )
        return data

    @classmethod
    def from_bytes(cls, data: bytes) -> Optional['BLEMeshMessage']:
        """Deserialize message from bytes."""
        try:
            parts = data.split(b'\x00', 3)
            if len(parts) < 4:
                return None

            message_id = parts[0].decode('utf-8')
            source_id = parts[1].decode('utf-8')
            destination_id = parts[2].decode('utf-8')

            # Extract payload and metadata
            remaining = parts[3]
            if len(remaining) < 12:  # timestamp (8) + ttl (4)
                return None

            payload = remaining[:-12]
            timestamp, ttl = struct.unpack('>dI', remaining[-12:])

            return cls(
                message_id=message_id,
                source_id=source_id,
                destination_id=destination_id,
                payload=payload,
                timestamp=timestamp,
                ttl=ttl
            )
        except (UnicodeDecodeError, struct.error):
            return None


class BLEEncryption:
    """Handles encryption for BLE mesh messages."""

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        self.public_key = self.private_key.public_key()

    def generate_shared_secret(self, peer_public_key_bytes: bytes) -> bytes:
        """Generate shared secret with peer."""
        try:
            peer_public_key = ec.EllipticCurvePublicKey.from_encoded_point(
                ec.SECP256R1(), peer_public_key_bytes
            )
            shared_key = self.private_key.exchange(ec.ECDH(), peer_public_key)

            # Derive encryption key
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=b'BLE-MESH-ENCRYPTION',
                backend=default_backend()
            )
            return hkdf.derive(shared_key)
        except Exception as e:
            logger.error(f"Failed to generate shared secret: {e}")
            return b''

    def encrypt_message(self, message: bytes, key: bytes) -> bytes:
        """Encrypt message using AES-GCM."""
        try:
            iv = os.urandom(12)
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(message) + encryptor.finalize()
            return iv + encryptor.tag + ciphertext
        except Exception as e:
            logger.error(f"Failed to encrypt message: {e}")
            return message

    def decrypt_message(self, encrypted_data: bytes, key: bytes) -> Optional[bytes]:
        """Decrypt message using AES-GCM."""
        try:
            if len(encrypted_data) < 28:  # iv(12) + tag(16) + min_ciphertext(0)
                return None

            iv = encrypted_data[:12]
            tag = encrypted_data[12:28]
            ciphertext = encrypted_data[28:]

            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            return decryptor.update(ciphertext) + decryptor.finalize()
        except Exception as e:
            logger.error(f"Failed to decrypt message: {e}")
            return None

    def get_public_key_bytes(self) -> bytes:
        """Get public key as bytes for sharing."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )


class BLEMeshNode:
    """
    Bluetooth LE Mesh Node for offline message transmission.

    Handles BLE advertising, scanning, and mesh routing with encryption.
    """

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.encryption = BLEEncryption(device_id)
        self.message_handlers: Dict[str, Callable] = {}
        self.routing_table: Dict[str, str] = {}  # destination -> next_hop
        self.message_cache: Dict[str, float] = {}  # message_id -> timestamp
        self.neighbors: Dict[str, float] = {}  # neighbor_id -> last_seen

        # BLE simulation (in real implementation, would use bleak or similar)
        self.advertising_data: List[bytes] = []
        self.scan_results: List[bytes] = []

    def register_message_handler(self, message_type: str, handler: Callable):
        """Register handler for specific message types."""
        self.message_handlers[message_type] = handler

    async def start_advertising(self, message: BLEMeshMessage):
        """Start BLE advertising with encrypted message."""
        try:
            # Encrypt message payload
            key = b'default_key_32_bytes_long_______'  # In real impl, use shared keys
            encrypted_payload = self.encryption.encrypt_message(message.payload, key)

            # Create encrypted message
            encrypted_message = BLEMeshMessage(
                message_id=message.message_id,
                source_id=message.source_id,
                destination_id=message.destination_id,
                payload=encrypted_payload,
                timestamp=message.timestamp,
                ttl=message.ttl - 1,
                hop_count=message.hop_count + 1
            )

            # Convert to advertising data
            advertising_bytes = encrypted_message.to_bytes()

            # Simulate BLE advertising (limit to 31 bytes for BLE spec)
            if len(advertising_bytes) <= 31:
                self.advertising_data.append(advertising_bytes)
                logger.info(f"Started advertising message {message.message_id}")
            else:
                logger.warning(f"Message too large for BLE advertising: {len(advertising_bytes)} bytes")

        except Exception as e:
            logger.error(f"Failed to start advertising: {e}")

    async def start_scanning(self):
        """Start BLE scanning for mesh messages."""
        try:
            while True:
                # Simulate receiving advertising data
                for advertising_bytes in self.advertising_data[:]:
                    await self._process_advertising_data(advertising_bytes)
                    self.advertising_data.remove(advertising_bytes)

                await asyncio.sleep(1.0)  # Scan interval

        except Exception as e:
            logger.error(f"Scanning failed: {e}")

    async def _process_advertising_data(self, data: bytes):
        """Process received BLE advertising data."""
        try:
            message = BLEMeshMessage.from_bytes(data)
            if not message:
                return

            # Check if message already processed
            if message.message_id in self.message_cache:
                return

            # Update cache
            self.message_cache[message.message_id] = time.time()

            # Check TTL
            if message.ttl <= 0:
                return

            # Decrypt payload
            key = b'default_key_32_bytes_long_______'  # In real impl, use shared keys
            decrypted_payload = self.encryption.decrypt_message(message.payload, key)
            if not decrypted_payload:
                return

            message.payload = decrypted_payload

            # Check if message is for us
            if message.destination_id == self.device_id:
                await self._handle_received_message(message)
            else:
                # Forward message
                await self._forward_message(message)

        except Exception as e:
            logger.error(f"Failed to process advertising data: {e}")

    async def _handle_received_message(self, message: BLEMeshMessage):
        """Handle message destined for this node."""
        try:
            # Extract message type from payload
            if len(message.payload) > 0:
                message_type = message.payload[0:1].decode('utf-8', errors='ignore')
                payload_data = message.payload[1:]

                # Call appropriate handler
                if message_type in self.message_handlers:
                    await self.message_handlers[message_type](message.source_id, payload_data)
                else:
                    logger.warning(f"No handler for message type: {message_type}")

        except Exception as e:
            logger.error(f"Failed to handle received message: {e}")

    async def _forward_message(self, message: BLEMeshMessage):
        """Forward message to next hop in mesh."""
        try:
            # Simple flooding for now (in real impl, use routing table)
            if message.ttl > 1:
                message.ttl -= 1
                message.hop_count += 1
                await self.start_advertising(message)

        except Exception as e:
            logger.error(f"Failed to forward message: {e}")

    async def send_message(self, destination_id: str, message_type: str, payload: bytes):
        """Send message to destination through mesh."""
        try:
            message = BLEMeshMessage(
                message_id=f"{self.device_id}_{int(time.time() * 1000)}",
                source_id=self.device_id,
                destination_id=destination_id,
                payload=message_type.encode('utf-8') + payload,
                timestamp=time.time(),
                ttl=64
            )

            await self.start_advertising(message)
            logger.info(f"Sent message {message.message_id} to {destination_id}")

        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics."""
        return {
            'device_id': self.device_id,
            'neighbors_count': len(self.neighbors),
            'messages_cached': len(self.message_cache),
            'advertising_active': len(self.advertising_data) > 0
        }


class BLEMeshNetwork:
    """
    Bluetooth LE Mesh Network coordinator.

    Manages multiple BLE mesh nodes and network-wide operations.
    """

    def __init__(self):
        self.nodes: Dict[str, BLEMeshNode] = {}
        self.network_topology: Dict[str, List[str]] = {}

    def add_node(self, device_id: str) -> BLEMeshNode:
        """Add a new node to the mesh network."""
        if device_id not in self.nodes:
            self.nodes[device_id] = BLEMeshNode(device_id)
            self.network_topology[device_id] = []
        return self.nodes[device_id]

    def connect_nodes(self, node1_id: str, node2_id: str):
        """Connect two nodes in the topology."""
        if node1_id in self.network_topology and node2_id in self.network_topology:
            if node2_id not in self.network_topology[node1_id]:
                self.network_topology[node1_id].append(node2_id)
            if node1_id not in self.network_topology[node2_id]:
                self.network_topology[node2_id].append(node1_id)

    async def broadcast_message(self, source_id: str, message_type: str, payload: bytes):
        """Broadcast message to all nodes in network."""
        if source_id in self.nodes:
            tasks = []
            for node_id in self.nodes:
                if node_id != source_id:
                    tasks.append(self.nodes[source_id].send_message(node_id, message_type, payload))

            await asyncio.gather(*tasks, return_exceptions=True)

    def get_network_topology(self) -> Dict[str, List[str]]:
        """Get current network topology."""
        return self.network_topology.copy()

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network-wide statistics."""
        total_messages = sum(len(node.message_cache) for node in self.nodes.values())
        total_neighbors = sum(len(node.neighbors) for node in self.nodes.values())

        return {
            'total_nodes': len(self.nodes),
            'total_messages_cached': total_messages,
            'total_neighbor_connections': total_neighbors,
            'network_topology': self.get_network_topology()
        }
