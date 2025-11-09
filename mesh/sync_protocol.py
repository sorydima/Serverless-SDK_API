"""
Mesh Data Synchronization Protocol

This module implements a protocol for synchronizing data between mesh network nodes
after one of them comes back online.
"""

import asyncio
import logging
import time
import json
import hashlib
from typing import Dict, List, Optional, Callable, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class SyncState(Enum):
    IDLE = "idle"
    REQUESTING = "requesting"
    RECEIVING = "receiving"
    SENDING = "sending"
    COMPLETED = "completed"
    FAILED = "failed"


class SyncPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class DataChunk:
    """Represents a chunk of data for synchronization."""
    chunk_id: str
    data: bytes
    checksum: str
    timestamp: float
    priority: SyncPriority = SyncPriority.NORMAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            'chunk_id': self.chunk_id,
            'data': self.data.hex(),
            'checksum': self.checksum,
            'timestamp': self.timestamp,
            'priority': self.priority.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataChunk':
        return cls(
            chunk_id=data['chunk_id'],
            data=bytes.fromhex(data['data']),
            checksum=data['checksum'],
            timestamp=data['timestamp'],
            priority=SyncPriority(data['priority'])
        )

    def calculate_checksum(self) -> str:
        """Calculate SHA256 checksum of data."""
        return hashlib.sha256(self.data).hexdigest()

    def verify_checksum(self) -> bool:
        """Verify data integrity."""
        return self.calculate_checksum() == self.checksum


@dataclass
class SyncSession:
    """Represents a synchronization session between nodes."""
    session_id: str
    requester_id: str
    provider_id: str
    data_type: str
    start_time: float
    last_activity: float
    state: SyncState = SyncState.IDLE
    total_chunks: int = 0
    transferred_chunks: int = 0
    failed_chunks: int = 0
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'requester_id': self.requester_id,
            'provider_id': self.provider_id,
            'data_type': self.data_type,
            'start_time': self.start_time,
            'last_activity': self.last_activity,
            'state': self.state.value,
            'total_chunks': self.total_chunks,
            'transferred_chunks': self.transferred_chunks,
            'failed_chunks': self.failed_chunks,
            'metadata': self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncSession':
        return cls(
            session_id=data['session_id'],
            requester_id=data['requester_id'],
            provider_id=data['provider_id'],
            data_type=data['data_type'],
            start_time=data['start_time'],
            last_activity=data['last_activity'],
            state=SyncState(data['state']),
            total_chunks=data.get('total_chunks', 0),
            transferred_chunks=data.get('transferred_chunks', 0),
            failed_chunks=data.get('failed_chunks', 0),
            metadata=data.get('metadata', {})
        )

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = time.time()

    def get_progress(self) -> float:
        """Get synchronization progress (0.0 to 1.0)."""
        if self.total_chunks == 0:
            return 0.0
        return self.transferred_chunks / self.total_chunks

    def is_completed(self) -> bool:
        """Check if synchronization is completed."""
        return (self.state == SyncState.COMPLETED or
                (self.total_chunks > 0 and self.transferred_chunks >= self.total_chunks))

    def is_failed(self) -> bool:
        """Check if synchronization has failed."""
        return self.state == SyncState.FAILED

    def is_active(self) -> bool:
        """Check if synchronization is currently active."""
        return self.state in [SyncState.REQUESTING, SyncState.RECEIVING, SyncState.SENDING]


@dataclass
class SyncManifest:
    """Manifest describing data available for synchronization."""
    data_type: str
    version: str
    total_size: int
    chunk_count: int
    checksum: str
    last_modified: float
    description: str = ""
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'data_type': self.data_type,
            'version': self.version,
            'total_size': self.total_size,
            'chunk_count': self.chunk_count,
            'checksum': self.checksum,
            'last_modified': self.last_modified,
            'description': self.description,
            'metadata': self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncManifest':
        return cls(
            data_type=data['data_type'],
            version=data['version'],
            total_size=data['total_size'],
            chunk_count=data['chunk_count'],
            checksum=data['checksum'],
            last_modified=data['last_modified'],
            description=data.get('description', ''),
            metadata=data.get('metadata', {})
        )


class MeshSyncProtocol:
    """
    Mesh Data Synchronization Protocol.

    Handles data synchronization between mesh network nodes when they come back online.
    """

    def __init__(self, node_id: str, mesh_network):
        self.node_id = node_id
        self.mesh_network = mesh_network
        self.active_sessions: Dict[str, SyncSession] = {}
        self.available_manifests: Dict[str, SyncManifest] = {}
        self.data_store: Dict[str, Dict[str, DataChunk]] = {}  # data_type -> {chunk_id -> chunk}
        self.sync_handlers: Dict[str, Callable] = {}

        # Message types
        self.MESSAGE_SYNC_REQUEST = "sync_request"
        self.MESSAGE_SYNC_RESPONSE = "sync_response"
        self.MESSAGE_SYNC_MANIFEST = "sync_manifest"
        self.MESSAGE_SYNC_CHUNK = "sync_chunk"
        self.MESSAGE_SYNC_ACK = "sync_ack"
        self.MESSAGE_SYNC_COMPLETE = "sync_complete"

        # Configuration
        self.chunk_size = 64 * 1024  # 64KB chunks
        self.max_concurrent_sessions = 3
        self.session_timeout = 300  # 5 minutes

        # Register message handlers
        self._register_message_handlers()

    def _register_message_handlers(self):
        """Register handlers for mesh network messages."""
        self.mesh_network.register_message_handler(self.MESSAGE_SYNC_REQUEST, self._handle_sync_request)
        self.mesh_network.register_message_handler(self.MESSAGE_SYNC_RESPONSE, self._handle_sync_response)
        self.mesh_network.register_message_handler(self.MESSAGE_SYNC_MANIFEST, self._handle_sync_manifest)
        self.mesh_network.register_message_handler(self.MESSAGE_SYNC_CHUNK, self._handle_sync_chunk)
        self.mesh_network.register_message_handler(self.MESSAGE_SYNC_ACK, self._handle_sync_ack)
        self.mesh_network.register_message_handler(self.MESSAGE_SYNC_COMPLETE, self._handle_sync_complete)

    def register_sync_handler(self, data_type: str, handler: Callable):
        """Register handler for specific data type synchronization."""
        self.sync_handlers[data_type] = handler

    def add_data_for_sync(self, data_type: str, data: bytes, description: str = "") -> str:
        """Add data to be made available for synchronization."""
        # Create chunks
        chunks = self._create_chunks(data, data_type)

        # Store chunks
        if data_type not in self.data_store:
            self.data_store[data_type] = {}
        self.data_store[data_type].update({chunk.chunk_id: chunk for chunk in chunks})

        # Create manifest
        total_size = len(data)
        checksum = hashlib.sha256(data).hexdigest()

        manifest = SyncManifest(
            data_type=data_type,
            version=f"v{int(time.time())}",
            total_size=total_size,
            chunk_count=len(chunks),
            checksum=checksum,
            last_modified=time.time(),
            description=description
        )

        self.available_manifests[data_type] = manifest
        logger.info(f"Added data for sync: {data_type} ({len(chunks)} chunks)")
        return data_type

    def _create_chunks(self, data: bytes, data_type: str) -> List[DataChunk]:
        """Split data into chunks for transmission."""
        chunks = []
        offset = 0
        chunk_index = 0

        while offset < len(data):
            chunk_data = data[offset:offset + self.chunk_size]
            chunk_id = f"{data_type}_chunk_{chunk_index}"

            chunk = DataChunk(
                chunk_id=chunk_id,
                data=chunk_data,
                checksum="",  # Will be calculated
                timestamp=time.time()
            )
            chunk.checksum = chunk.calculate_checksum()

            chunks.append(chunk)
            offset += len(chunk_data)
            chunk_index += 1

        return chunks

    async def request_sync(self, provider_id: str, data_type: str) -> Optional[str]:
        """Request synchronization of data from another node."""
        if len(self.active_sessions) >= self.max_concurrent_sessions:
            logger.warning("Maximum concurrent sync sessions reached")
            return None

        session_id = f"sync_{self.node_id}_{provider_id}_{data_type}_{int(time.time())}"

        session = SyncSession(
            session_id=session_id,
            requester_id=self.node_id,
            provider_id=provider_id,
            data_type=data_type,
            start_time=time.time(),
            last_activity=time.time(),
            state=SyncState.REQUESTING
        )

        self.active_sessions[session_id] = session

        # Send sync request
        request_data = {
            'session_id': session_id,
            'data_type': data_type,
            'requester': self.node_id,
            'timestamp': time.time()
        }

        await self.mesh_network.send_message(
            provider_id,
            self.MESSAGE_SYNC_REQUEST,
            json.dumps(request_data).encode()
        )

        logger.info(f"Requested sync session: {session_id}")
        return session_id

    async def get_sync_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a synchronization session."""
        if session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]

        return {
            'session_id': session_id,
            'state': session.state.value,
            'progress': session.get_progress(),
            'transferred_chunks': session.transferred_chunks,
            'total_chunks': session.total_chunks,
            'failed_chunks': session.failed_chunks,
            'data_type': session.data_type,
            'provider': session.provider_id,
            'start_time': session.start_time,
            'last_activity': session.last_activity
        }

    async def cancel_sync(self, session_id: str):
        """Cancel a synchronization session."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.state = SyncState.FAILED

            # Notify provider
            cancel_data = {
                'session_id': session_id,
                'reason': 'cancelled_by_requester',
                'timestamp': time.time()
            }

            await self.mesh_network.send_message(
                session.provider_id,
                self.MESSAGE_SYNC_COMPLETE,
                json.dumps(cancel_data).encode()
            )

            logger.info(f"Cancelled sync session: {session_id}")

    async def _handle_sync_request(self, sender_id: str, payload: bytes):
        """Handle synchronization request."""
        try:
            data = json.loads(payload.decode())
            session_id = data['session_id']
            data_type = data['data_type']
            requester = data['requester']

            if data_type in self.available_manifests:
                manifest = self.available_manifests[data_type]

                # Create session
                session = SyncSession(
                    session_id=session_id,
                    requester_id=requester,
                    provider_id=self.node_id,
                    data_type=data_type,
                    start_time=time.time(),
                    last_activity=time.time(),
                    state=SyncState.SENDING,
                    total_chunks=manifest.chunk_count
                )

                self.active_sessions[session_id] = session

                # Send manifest
                await self._send_manifest(session, manifest)
            else:
                # Send rejection
                response_data = {
                    'session_id': session_id,
                    'status': 'rejected',
                    'reason': 'data_not_available',
                    'timestamp': time.time()
                }

                await self.mesh_network.send_message(
                    requester,
                    self.MESSAGE_SYNC_RESPONSE,
                    json.dumps(response_data).encode()
                )

        except Exception as e:
            logger.error(f"Error handling sync request: {e}")

    async def _handle_sync_response(self, sender_id: str, payload: bytes):
        """Handle synchronization response."""
        try:
            data = json.loads(payload.decode())
            session_id = data['session_id']
            status = data['status']

            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]

                if status == 'accepted':
                    session.state = SyncState.RECEIVING
                    session.update_activity()
                else:
                    session.state = SyncState.FAILED
                    logger.warning(f"Sync request rejected: {data.get('reason', 'unknown')}")

        except Exception as e:
            logger.error(f"Error handling sync response: {e}")

    async def _handle_sync_manifest(self, sender_id: str, payload: bytes):
        """Handle synchronization manifest."""
        try:
            data = json.loads(payload.decode())
            session_id = data['session_id']
            manifest_data = data['manifest']

            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                manifest = SyncManifest.from_dict(manifest_data)

                session.total_chunks = manifest.chunk_count
                session.state = SyncState.RECEIVING
                session.update_activity()

                # Request chunks
                await self._request_chunks(session)

        except Exception as e:
            logger.error(f"Error handling sync manifest: {e}")

    async def _handle_sync_chunk(self, sender_id: str, payload: bytes):
        """Handle data chunk reception."""
        try:
            data = json.loads(payload.decode())
            session_id = data['session_id']
            chunk_data = data['chunk']

            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                chunk = DataChunk.from_dict(chunk_data)

                # Verify chunk
                if chunk.verify_checksum():
                    # Store chunk
                    if session.data_type not in self.data_store:
                        self.data_store[session.data_type] = {}
                    self.data_store[session.data_type][chunk.chunk_id] = chunk

                    session.transferred_chunks += 1
                    session.update_activity()

                    # Send acknowledgment
                    ack_data = {
                        'session_id': session_id,
                        'chunk_id': chunk.chunk_id,
                        'status': 'received',
                        'timestamp': time.time()
                    }

                    await self.mesh_network.send_message(
                        session.provider_id,
                        self.MESSAGE_SYNC_ACK,
                        json.dumps(ack_data).encode()
                    )

                    # Check if complete
                    if session.transferred_chunks >= session.total_chunks:
                        await self._complete_sync(session)
                else:
                    session.failed_chunks += 1
                    logger.warning(f"Chunk checksum failed: {chunk.chunk_id}")

        except Exception as e:
            logger.error(f"Error handling sync chunk: {e}")

    async def _handle_sync_ack(self, sender_id: str, payload: bytes):
        """Handle chunk acknowledgment."""
        try:
            data = json.loads(payload.decode())
            session_id = data['session_id']
            chunk_id = data['chunk_id']

            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.transferred_chunks += 1
                session.update_activity()

                # Send next chunk if available
                if session.state == SyncState.SENDING:
                    await self._send_next_chunk(session)

        except Exception as e:
            logger.error(f"Error handling sync ack: {e}")

    async def _handle_sync_complete(self, sender_id: str, payload: bytes):
        """Handle synchronization completion."""
        try:
            data = json.loads(payload.decode())
            session_id = data['session_id']
            reason = data.get('reason', 'completed')

            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]

                if reason == 'completed':
                    session.state = SyncState.COMPLETED
                    await self._process_completed_sync(session)
                else:
                    session.state = SyncState.FAILED

                logger.info(f"Sync session {session_id} {reason}")

        except Exception as e:
            logger.error(f"Error handling sync complete: {e}")

    async def _send_manifest(self, session: SyncSession, manifest: SyncManifest):
        """Send manifest to requester."""
        manifest_data = {
            'session_id': session.session_id,
            'manifest': manifest.to_dict(),
            'timestamp': time.time()
        }

        await self.mesh_network.send_message(
            session.requester_id,
            self.MESSAGE_SYNC_MANIFEST,
            json.dumps(manifest_data).encode()
        )

    async def _request_chunks(self, session: SyncSession):
        """Request data chunks from provider."""
        # For simplicity, request all chunks at once
        # In real implementation, this would be done incrementally
        request_data = {
            'session_id': session.session_id,
            'requested_chunks': list(range(session.total_chunks)),
            'timestamp': time.time()
        }

        await self.mesh_network.send_message(
            session.provider_id,
            self.MESSAGE_SYNC_REQUEST,
            json.dumps(request_data).encode()
        )

    async def _send_next_chunk(self, session: SyncSession):
        """Send next chunk to requester."""
        if session.data_type in self.data_store:
            chunks = list(self.data_store[session.data_type].values())

            if session.transferred_chunks < len(chunks):
                chunk = chunks[session.transferred_chunks]

                chunk_data = {
                    'session_id': session.session_id,
                    'chunk': chunk.to_dict(),
                    'timestamp': time.time()
                }

                await self.mesh_network.send_message(
                    session.requester_id,
                    self.MESSAGE_SYNC_CHUNK,
                    json.dumps(chunk_data).encode()
                )

    async def _complete_sync(self, session: SyncSession):
        """Complete synchronization and process data."""
        session.state = SyncState.COMPLETED

        # Reassemble data
        if session.data_type in self.data_store:
            chunks = self.data_store[session.data_type]
            sorted_chunks = sorted(chunks.values(), key=lambda c: c.chunk_id)

            assembled_data = b''.join(chunk.data for chunk in sorted_chunks)

            # Call sync handler
            if session.data_type in self.sync_handlers:
                await self.sync_handlers[session.data_type](session.data_type, assembled_data)

        # Notify completion
        complete_data = {
            'session_id': session.session_id,
            'reason': 'completed',
            'timestamp': time.time()
        }

        await self.mesh_network.send_message(
            session.provider_id,
            self.MESSAGE_SYNC_COMPLETE,
            json.dumps(complete_data).encode()
        )

        logger.info(f"Completed sync session: {session.session_id}")

    async def _process_completed_sync(self, session: SyncSession):
        """Process completed synchronization."""
        # Call sync handler if available
        if session.data_type in self.sync_handlers:
            # Reassemble data for handler
            if session.data_type in self.data_store:
                chunks = self.data_store[session.data_type]
                sorted_chunks = sorted(chunks.values(), key=lambda c: c.chunk_id)
                assembled_data = b''.join(chunk.data for chunk in sorted_chunks)

                await self.sync_handlers[session.data_type](session.data_type, assembled_data)

    async def cleanup_expired_sessions(self):
        """Clean up expired synchronization sessions."""
        current_time = time.time()
        expired_sessions = []

        for session_id, session in self.active_sessions.items():
            if current_time - session.last_activity > self.session_timeout:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            session = self.active_sessions[session_id]
            session.state = SyncState.FAILED
            del self.active_sessions[session_id]
            logger.warning(f"Cleaned up expired sync session: {session_id}")

    def get_available_data_types(self) -> List[str]:
        """Get list of data types available for synchronization."""
        return list(self.available_manifests.keys())

    def get_sync_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics."""
        active_sessions = len([s for s in self.active_sessions.values() if s.is_active()])
        completed_sessions = len([s for s in self.active_sessions.values() if s.is_completed()])
        failed_sessions = len([s for s in self.active_sessions.values() if s.is_failed()])

        return {
            'node_id': self.node_id,
            'available_data_types': len(self.available_manifests),
            'active_sessions': active_sessions,
            'completed_sessions': completed_sessions,
            'failed_sessions': failed_sessions,
            'total_sessions': len(self.active_sessions)
        }


class MeshSyncNetwork:
    """
    Mesh Synchronization Network coordinator.

    Manages synchronization across multiple mesh nodes.
    """

    def __init__(self, mesh_network):
        self.mesh_network = mesh_network
        self.sync_protocols: Dict[str, MeshSyncProtocol] = {}

    def add_sync_protocol(self, node_id: str) -> MeshSyncProtocol:
        """Add synchronization protocol for a node."""
        if node_id not in self.sync_protocols:
            self.sync_protocols[node_id] = MeshSyncProtocol(node_id, self.mesh_network)
        return self.sync_protocols[node_id]

    async def broadcast_data_availability(self, data_type: str, description: str = ""):
        """Broadcast that data is available for synchronization."""
        for protocol in self.sync_protocols.values():
            if data_type in protocol.available_manifests:
                manifest = protocol.available_manifests[data_type]

                broadcast_data = {
                    'data_type': data_type,
                    'manifest': manifest.to_dict(),
                    'provider': protocol.node_id,
                    'timestamp': time.time()
                }

                await self.mesh_network.broadcast_message(
                    "sync_data_available",
                    json.dumps(broadcast_data).encode()
                )
                break

    async def request_network_sync(self, data_type: str) -> List[str]:
        """Request synchronization of data across the network."""
        session_ids = []

        for protocol in self.sync_protocols.values():
            # Find a provider that has the data
            for node_id, other_protocol in self.sync_protocols.items():
                if node_id != protocol.node_id and data_type in other_protocol.available_manifests:
                    session_id = await protocol.request_sync(node_id, data_type)
                    if session_id:
                        session_ids.append(session_id)
                    break

        return session_ids

    def get_network_sync_stats(self) -> Dict[str, Any]:
        """Get network-wide synchronization statistics."""
        protocol_stats = [protocol.get_sync_stats() for protocol in self.sync_protocols.values()]

        total_available = sum(stats['available_data_types'] for stats in protocol_stats)
        total_active = sum(stats['active_sessions'] for stats in protocol_stats)
        total_completed = sum(stats['completed_sessions'] for stats in protocol_stats)

        return {
            'total_protocols': len(self.sync_protocols),
            'total_available_data_types': total_available,
            'total_active_sessions': total_active,
            'total_completed_sessions': total_completed,
            'protocol_stats': protocol_stats
        }
