"""Common blockchain bridge interface and simple utilities.

Bridges for different networks should implement the BlockchainBridge
interface below (connect/disconnect/ping/get_stats).
"""
import abc
from typing import Dict, Any


class BlockchainBridge(abc.ABC):
    @abc.abstractmethod
    async def connect(self) -> bool:
        pass

    @abc.abstractmethod
    async def disconnect(self) -> None:
        pass

    @abc.abstractmethod
    async def ping(self) -> bool:
        pass

    @abc.abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        pass


__all__ = ["BlockchainBridge"]
