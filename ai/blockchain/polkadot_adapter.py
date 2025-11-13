"""Adapter for Polkadot bridge that fits the BlockchainBridge interface.

If `ai.blockchain.polkadot.bridge.PolkadotBridge` is available and
its dependencies are installed, we wrap it; otherwise we provide a
lightweight in-memory mock implementation suitable for tests.
"""
import asyncio
import logging
from typing import Dict, Any, Optional

from .bridge_base import BlockchainBridge

logger = logging.getLogger(__name__)

try:
    from .polkadot.bridge import PolkadotBridge as _RealPolkadotBridge  # type: ignore
    _HAS_REAL = True
except Exception:
    _HAS_REAL = False


class PolkadotAdapter(BlockchainBridge):
    def __init__(self, endpoint: str = "wss://rpc.polkadot.io", keypair_uri: str = "//Alice"):
        self.endpoint = endpoint
        self.keypair_uri = keypair_uri
        if _HAS_REAL:
            try:
                self._real = _RealPolkadotBridge(endpoint=endpoint, keypair_uri=keypair_uri)
            except Exception as e:
                logger.warning(f"Failed to init real PolkadotBridge: {e}")
                self._real = None
        else:
            self._real = None

        # In-memory store for recorded hashes when real bridge not available
        self._pending = []
        self._confirmed = {}
        self.connected = False

    async def connect(self) -> bool:
        if self._real:
            try:
                ok = await self._real.connect()
                self.connected = ok
                return ok
            except Exception:
                self.connected = False
                return False

        # Mock connect
        await asyncio.sleep(0.01)
        self.connected = True
        return True

    async def disconnect(self) -> None:
        if self._real:
            await self._real.disconnect()
            self.connected = False
            return
        self.connected = False

    async def ping(self) -> bool:
        if self._real:
            try:
                # Real class doesn't have ping, use get_bridge_stats as proxy
                stats = self._real.get_bridge_stats()
                return stats.get('connected', False)
            except Exception:
                return False
        await asyncio.sleep(0.005)
        return self.connected

    def get_stats(self) -> Dict[str, Any]:
        if self._real:
            try:
                return self._real.get_bridge_stats()
            except Exception:
                pass
        return {'network': 'Polkadot (mock)', 'endpoint': self.endpoint, 'connected': self.connected,
                'pending_hashes': len(self._pending), 'confirmed_hashes': len(self._confirmed)}

    # Minimal compatibility function for recording a hash in mock
    async def record_message_hash(self, message_id: str, message_type: str, message_data: Any, metadata: Dict[str, Any] = None) -> bool:
        if self._real:
            try:
                return await self._real.record_message_hash(message_id, message_type, message_data, metadata or {})
            except Exception:
                return False

        from hashlib import sha256
        import json
        if isinstance(message_data, dict):
            message_data = json.dumps(message_data, sort_keys=True)
        if isinstance(message_data, str):
            message_data = message_data.encode('utf-8')
        hv = sha256(message_data).hexdigest()
        entry = {'message_id': message_id, 'message_type': message_type, 'hash_value': hv, 'metadata': metadata or {}}
        self._pending.append(entry)
        # Simulate immediate confirmation for tests
        self._confirmed[message_id] = entry
        return True


__all__ = ["PolkadotAdapter"]
