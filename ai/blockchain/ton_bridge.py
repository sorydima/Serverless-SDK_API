"""Mock TON bridge implementation (lightweight).
"""
import asyncio
from typing import Dict, Any
from .bridge_base import BlockchainBridge


class TONBridge(BlockchainBridge):
    def __init__(self, endpoint: str = "https://ton.example"):
        self.endpoint = endpoint
        self.connected = False

    async def connect(self) -> bool:
        await asyncio.sleep(0.01)
        self.connected = True
        return True

    async def disconnect(self) -> None:
        self.connected = False

    async def ping(self) -> bool:
        # Simulate a lightweight network check
        await asyncio.sleep(0.005)
        return self.connected

    def get_stats(self) -> Dict[str, Any]:
        return {'network': 'TON', 'endpoint': self.endpoint, 'connected': self.connected}


__all__ = ["TONBridge"]
