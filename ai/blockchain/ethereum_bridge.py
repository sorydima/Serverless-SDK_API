"""Mock Ethereum bridge implementation (lightweight).
"""
import asyncio
from typing import Dict, Any
from .bridge_base import BlockchainBridge


class EthereumBridge(BlockchainBridge):
    def __init__(self, endpoint: str = "https://eth.example"):
        self.endpoint = endpoint
        self.connected = False

    async def connect(self) -> bool:
        await asyncio.sleep(0.01)
        self.connected = True
        return True

    async def disconnect(self) -> None:
        self.connected = False

    async def ping(self) -> bool:
        await asyncio.sleep(0.005)
        return self.connected

    def get_stats(self) -> Dict[str, Any]:
        return {'network': 'Ethereum', 'endpoint': self.endpoint, 'connected': self.connected}


__all__ = ["EthereumBridge"]
