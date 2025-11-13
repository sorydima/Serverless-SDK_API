"""
Qubit Encryption Module for quantum-secure communication between nodes.
Implements quantum key distribution and encryption protocols.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import hashlib
import secrets
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QuantumKey:
    """Represents a quantum-generated key."""
    key_id: str
    key_data: bytes
    length: int
    source_node: str
    target_node: str
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'key_id': self.key_id,
            'key_data': self.key_data.hex(),
            'length': self.length,
            'source_node': self.source_node,
            'target_node': self.target_node,
            'timestamp': self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuantumKey':
        return cls(
            key_id=data['key_id'],
            key_data=bytes.fromhex(data['key_data']),
            length=data['length'],
            source_node=data['source_node'],
            target_node=data['target_node'],
            timestamp=data['timestamp']
        )

class QubitEncryption:
    """
    Implements quantum encryption protocols for secure node-to-node communication.
    """

    def __init__(self):
        self.keys: Dict[str, QuantumKey] = {}
        self.active_sessions: Dict[str, str] = {}  # session_id -> key_id

    def generate_quantum_key(self, source_node: str, target_node: str,
                           key_length: int = 256) -> QuantumKey:
        """
        Generate a quantum key using simplified BB84 protocol simulation.

        Args:
            source_node: Source node identifier
            target_node: Target node identifier
            key_length: Desired key length in bits

        Returns:
            QuantumKey: Generated quantum key
        """
        # Simulate BB84 protocol
        raw_bits = self._generate_raw_bits(key_length * 2)  # Generate extra for error correction
        bases = self._generate_bases(key_length * 2)

        # Simulate measurement by target
        target_bases = self._generate_bases(key_length * 2)
        measured_bits = self._measure_bits(raw_bits, bases, target_bases)

        # Basis reconciliation (keep bits where bases match)
        reconciled_bits = []
        reconciled_bases = []

        for i, (bit, source_base, target_base) in enumerate(zip(measured_bits, bases, target_bases)):
            if source_base == target_base:
                reconciled_bits.append(bit)
                reconciled_bases.append(source_base)

        # Error correction and privacy amplification
        final_key_bits = self._privacy_amplification(reconciled_bits[:key_length])

        # Convert to bytes
        key_bytes = self._bits_to_bytes(final_key_bits)

        key_id = f"qk_{source_node}_{target_node}_{secrets.token_hex(8)}"

        quantum_key = QuantumKey(
            key_id=key_id,
            key_data=key_bytes,
            length=len(final_key_bits),
            source_node=source_node,
            target_node=target_node,
            timestamp=np.datetime64('now').astype(float)
        )

        self.keys[key_id] = quantum_key
        return quantum_key

    def _generate_raw_bits(self, length: int) -> List[int]:
        """Generate random bits (0 or 1)."""
        return [secrets.randbelow(2) for _ in range(length)]

    def _generate_bases(self, length: int) -> List[str]:
        """Generate random bases (+ or x)."""
        return [secrets.choice(['+', 'x']) for _ in range(length)]

    def _measure_bits(self, bits: List[int], source_bases: List[str],
                     target_bases: List[str]) -> List[int]:
        """Simulate quantum measurement."""
        measured = []
        for bit, source_base, target_base in zip(bits, source_bases, target_bases):
            if source_base == target_base:
                # Correct basis: measure correctly
                measured.append(bit)
            else:
                # Wrong basis: random measurement
                measured.append(secrets.randbelow(2))
        return measured

    def _privacy_amplification(self, bits: List[int]) -> List[int]:
        """Apply privacy amplification to reduce information leakage."""
        # Simple hash-based privacy amplification
        bit_string = ''.join(map(str, bits))
        hash_obj = hashlib.sha256(bit_string.encode())
        hash_bits = bin(int(hash_obj.hexdigest(), 16))[2:].zfill(256)
        return [int(b) for b in hash_bits[:len(bits)]]

    def _bits_to_bytes(self, bits: List[int]) -> bytes:
        """Convert bit list to bytes."""
        byte_list = []
        for i in range(0, len(bits), 8):
            byte_bits = bits[i:i+8]
            byte_value = sum(bit << (7 - j) for j, bit in enumerate(byte_bits))
            byte_list.append(byte_value)
        return bytes(byte_list)

    def encrypt_message(self, message: bytes, key_id: str) -> Tuple[bytes, str]:
        """
        Encrypt a message using quantum key.

        Args:
            message: Message to encrypt
            key_id: Quantum key identifier

        Returns:
            Tuple of (encrypted_message, session_id)
        """
        if key_id not in self.keys:
            raise ValueError(f"Quantum key {key_id} not found")

        key = self.keys[key_id]

        # Use quantum key for one-time pad encryption
        encrypted = bytes(a ^ b for a, b in zip(message, key.key_data * (len(message) // len(key.key_data) + 1)))

        session_id = f"session_{secrets.token_hex(16)}"
        self.active_sessions[session_id] = key_id

        return encrypted, session_id

    def decrypt_message(self, encrypted_message: bytes, session_id: str) -> bytes:
        """
        Decrypt a message using quantum key from session.

        Args:
            encrypted_message: Encrypted message
            session_id: Session identifier

        Returns:
            Decrypted message
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        key_id = self.active_sessions[session_id]
        key = self.keys[key_id]

        # One-time pad decryption (same as encryption)
        decrypted = bytes(a ^ b for a, b in zip(encrypted_message, key.key_data * (len(encrypted_message) // len(key.key_data) + 1)))

        return decrypted

    def establish_secure_channel(self, node1: str, node2: str) -> str:
        """
        Establish a secure quantum channel between two nodes.

        Args:
            node1: First node identifier
            node2: Second node identifier

        Returns:
            Channel identifier
        """
        # Generate quantum key for the channel
        key = self.generate_quantum_key(node1, node2)

        channel_id = f"channel_{node1}_{node2}_{secrets.token_hex(8)}"
        logger.info(f"Established quantum secure channel {channel_id} between {node1} and {node2}")

        return channel_id

    def get_key_info(self, key_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a quantum key."""
        if key_id in self.keys:
            return self.keys[key_id].to_dict()
        return None

    def list_keys(self) -> List[Dict[str, Any]]:
        """List all quantum keys."""
        return [key.to_dict() for key in self.keys.values()]

    def revoke_key(self, key_id: str) -> bool:
        """Revoke a quantum key."""
        if key_id in self.keys:
            del self.keys[key_id]
            # Remove from active sessions
            sessions_to_remove = [s for s, k in self.active_sessions.items() if k == key_id]
            for session in sessions_to_remove:
                del self.active_sessions[session]
            return True
        return False

# Integration with mesh networking
class QuantumSecureMesh:
    """
    Integrates quantum encryption with mesh networking layer.
    """

    def __init__(self, encryption: QubitEncryption):
        self.encryption = encryption
        self.node_keys: Dict[str, str] = {}  # node -> key_id

    def register_node(self, node_id: str):
        """Register a node for quantum encryption."""
        # Generate a master key for the node (simplified)
        master_key = self.encryption.generate_quantum_key("master", node_id, 512)
        self.node_keys[node_id] = master_key.key_id

    def send_secure_message(self, from_node: str, to_node: str, message: bytes) -> Tuple[bytes, str]:
        """
        Send an encrypted message between nodes.

        Args:
            from_node: Sender node
            to_node: Receiver node
            message: Message to send

        Returns:
            Tuple of (encrypted_message, session_id)
        """
        # Establish or reuse quantum key
        channel_key = self.encryption.generate_quantum_key(from_node, to_node)
        return self.encryption.encrypt_message(message, channel_key.key_id)

    def receive_secure_message(self, encrypted_message: bytes, session_id: str) -> bytes:
        """
        Receive and decrypt a secure message.

        Args:
            encrypted_message: Encrypted message
            session_id: Session identifier

        Returns:
            Decrypted message
        """
        return self.encryption.decrypt_message(encrypted_message, session_id)
