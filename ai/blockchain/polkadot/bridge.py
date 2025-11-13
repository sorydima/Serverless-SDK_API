"""
Polkadot Bridge for Mesh Network Message Hash Recording

This module extends the Polkadot integration to record cryptographic hashes
of mesh network messages on the blockchain for immutability and verification.
"""

import asyncio
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime

try:
    from substrateinterface import SubstrateInterface
    from substrateinterface.exceptions import SubstrateRequestException
    _HAS_SUBSTRATE = True
except ImportError:
    _HAS_SUBSTRATE = False
    SubstrateInterface = None

logger = logging.getLogger(__name__)


@dataclass
class MessageHash:
    """Represents a message hash to be recorded on blockchain."""
    message_id: str
    message_type: str  # 'vote', 'routing', 'sync', etc.
    hash_value: str
    timestamp: float
    metadata: Dict[str, Any]
    signature: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_id': self.message_id,
            'message_type': self.message_type,
            'hash_value': self.hash_value,
            'timestamp': self.timestamp,
            'metadata': self.metadata,
            'signature': self.signature
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageHash':
        return cls(
            message_id=data['message_id'],
            message_type=data['message_type'],
            hash_value=data['hash_value'],
            timestamp=data['timestamp'],
            metadata=data.get('metadata', {}),
            signature=data.get('signature')
        )


class PolkadotBridge:
    """
    Polkadot Bridge for recording mesh message hashes.

    Provides functionality to submit message hashes to Polkadot/Substrate
    blockchain for immutable record keeping and cross-chain verification.
    """

    def __init__(self, endpoint: str = "wss://rpc.polkadot.io",
                 keypair_uri: str = "//Alice"):
        if not _HAS_SUBSTRATE:
            raise ImportError("py-substrate-interface is required for Polkadot bridge")

        self.endpoint = endpoint
        self.keypair_uri = keypair_uri
        self.substrate = None
        self.keypair = None
        self.is_connected = False

        # Message hash storage
        self.pending_hashes: List[MessageHash] = []
        self.confirmed_hashes: Dict[str, MessageHash] = {}

        # Bridge configuration
        self.batch_size = 10  # Submit in batches
        self.retry_attempts = 3
        self.confirmation_blocks = 6  # Wait for 6 block confirmations

    async def connect(self) -> bool:
        """Connect to Polkadot network."""
        try:
            self.substrate = SubstrateInterface(url=self.endpoint)
            self.keypair = self.substrate.create_keypair_from_uri(self.keypair_uri)
            self.is_connected = True
            logger.info(f"Connected to Polkadot network at {self.endpoint}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Polkadot: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Disconnect from Polkadot network."""
        if self.substrate:
            self.substrate.close()
            self.is_connected = False
            logger.info("Disconnected from Polkadot network")

    def calculate_message_hash(self, message_data: Union[str, bytes, Dict]) -> str:
        """Calculate SHA-256 hash of message data."""
        if isinstance(message_data, dict):
            message_data = json.dumps(message_data, sort_keys=True)

        if isinstance(message_data, str):
            message_data = message_data.encode('utf-8')

        return hashlib.sha256(message_data).hexdigest()

    async def record_message_hash(self, message_id: str, message_type: str,
                                message_data: Union[str, bytes, Dict],
                                metadata: Dict[str, Any] = None) -> bool:
        """
        Record a message hash on the blockchain.

        Args:
            message_id: Unique identifier for the message
            message_type: Type of message ('vote', 'routing', 'sync', etc.)
            message_data: The actual message data to hash
            metadata: Additional metadata about the message

        Returns:
            bool: True if successfully recorded
        """
        if not self.is_connected:
            logger.error("Not connected to Polkadot network")
            return False

        try:
            hash_value = self.calculate_message_hash(message_data)

            message_hash = MessageHash(
                message_id=message_id,
                message_type=message_type,
                hash_value=hash_value,
                timestamp=datetime.now().timestamp(),
                metadata=metadata or {}
            )

            # Add to pending queue
            self.pending_hashes.append(message_hash)

            # Submit if batch size reached
            if len(self.pending_hashes) >= self.batch_size:
                await self._submit_batch()

            logger.info(f"Queued message hash for recording: {message_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to record message hash: {e}")
            return False

    async def _submit_batch(self):
        """Submit a batch of message hashes to the blockchain."""
        if not self.pending_hashes:
            return

        try:
            # Prepare batch data
            batch_data = {
                'hashes': [mh.to_dict() for mh in self.pending_hashes],
                'batch_id': f"batch_{int(datetime.now().timestamp())}",
                'submitter': self.keypair.ss58_address
            }

            # Create extrinsic call
            call = self.substrate.compose_call(
                call_module='System',
                call_function='remark',
                call_params={
                    'remark': json.dumps(batch_data).encode()
                }
            )

            # Create signed extrinsic
            extrinsic = self.substrate.create_signed_extrinsic(
                call=call,
                keypair=self.keypair
            )

            # Submit extrinsic
            result = self.substrate.submit_extrinsic(extrinsic, wait_for_inclusion=True)

            if result.is_success:
                # Move to confirmed hashes
                for mh in self.pending_hashes:
                    self.confirmed_hashes[mh.message_id] = mh

                logger.info(f"Successfully submitted batch of {len(self.pending_hashes)} message hashes")
                self.pending_hashes.clear()
            else:
                logger.error(f"Failed to submit batch: {result.error_message}")

        except Exception as e:
            logger.error(f"Error submitting batch: {e}")

    async def verify_message_hash(self, message_id: str) -> Optional[MessageHash]:
        """
        Verify if a message hash exists on the blockchain.

        Args:
            message_id: The message ID to verify

        Returns:
            MessageHash if found, None otherwise
        """
        if not self.is_connected:
            return None

        # Check local cache first
        if message_id in self.confirmed_hashes:
            return self.confirmed_hashes[message_id]

        # TODO: Implement blockchain query for verification
        # This would require querying the chain for the remark extrinsics
        # and parsing the batch data

        return None

    async def get_message_hashes_by_type(self, message_type: str) -> List[MessageHash]:
        """Get all recorded message hashes of a specific type."""
        return [mh for mh in self.confirmed_hashes.values()
                if mh.message_type == message_type]

    async def get_recent_hashes(self, limit: int = 100) -> List[MessageHash]:
        """Get most recent message hashes."""
        sorted_hashes = sorted(
            self.confirmed_hashes.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )
        return sorted_hashes[:limit]

    def get_bridge_stats(self) -> Dict[str, Any]:
        """Get bridge statistics."""
        return {
            'connected': self.is_connected,
            'endpoint': self.endpoint,
            'pending_hashes': len(self.pending_hashes),
            'confirmed_hashes': len(self.confirmed_hashes),
            'account_address': self.keypair.ss58_address if self.keypair else None
        }


class MeshMessageRecorder:
    """
    Recorder for mesh network messages using Polkadot bridge.

    Integrates with mesh network components to automatically record
    message hashes for voting, routing, and synchronization.
    """

    def __init__(self, bridge: PolkadotBridge):
        self.bridge = bridge
        self.recorded_messages: Dict[str, MessageHash] = {}

    async def record_vote_message(self, vote_data: Dict[str, Any]) -> bool:
        """Record a voting message hash."""
        message_id = f"vote_{vote_data.get('voter_id')}_{vote_data.get('session_id')}_{int(datetime.now().timestamp())}"
        return await self.bridge.record_message_hash(
            message_id=message_id,
            message_type='vote',
            message_data=vote_data,
            metadata={'session_id': vote_data.get('session_id')}
        )

    async def record_routing_message(self, routing_data: Dict[str, Any]) -> bool:
        """Record a routing message hash."""
        message_id = f"routing_{routing_data.get('source')}_{routing_data.get('destination')}_{int(datetime.now().timestamp())}"
        return await self.bridge.record_message_hash(
            message_id=message_id,
            message_type='routing',
            message_data=routing_data,
            metadata={'algorithm': routing_data.get('algorithm', 'unknown')}
        )

    async def record_sync_message(self, sync_data: Dict[str, Any]) -> bool:
        """Record a synchronization message hash."""
        message_id = f"sync_{sync_data.get('node_id')}_{sync_data.get('sync_type')}_{int(datetime.now().timestamp())}"
        return await self.bridge.record_message_hash(
            message_id=message_id,
            message_type='sync',
            message_data=sync_data,
            metadata={'sync_type': sync_data.get('sync_type')}
        )

    async def verify_message_integrity(self, message_id: str, message_data: Dict[str, Any]) -> bool:
        """Verify message integrity against blockchain record."""
        recorded_hash = await self.bridge.verify_message_hash(message_id)
        if not recorded_hash:
            return False

        current_hash = self.bridge.calculate_message_hash(message_data)
        return current_hash == recorded_hash.hash_value
