"""Lightweight MCP client shim and in-process simulator for tests.

This provides a minimal async MCPClient interface used by adapters
in this repository. It uses an in-process simulator (asyncio.Queue)
when no external MCP server is provided.
"""
import asyncio
from typing import Any, Dict, Optional


class MCPClient:
    """Minimal MCP client.

    If host is None (default), operate in local simulator mode.
    """

    def __init__(self, host: Optional[str] = None, port: int = 0):
        self.host = host
        self.port = port
        self._sim_queue: Optional[asyncio.Queue] = None

        if self.host is None:
            # local simulator
            self._sim_queue = asyncio.Queue()

    async def send_prompt(self, model: str, prompt: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a prompt to an LLM. Returns a dict with reply and metadata.

        In simulator mode this just echoes input with a simulated response.
        """
        metadata = metadata or {}
        if self._sim_queue is not None:
            # Simulate processing delay
            await asyncio.sleep(0.01)
            reply = f"[simulated-{model}] {prompt[::-1]}"  # simple transform
            response = {
                'model': model,
                'prompt': prompt,
                'reply': reply,
                'metadata': metadata
            }
            return response

        # Real client would call networked MCP here. For now, raise.
        raise RuntimeError("Remote MCP client not implemented in this shim")

    async def close(self):
        return None


__all__ = ["MCPClient"]
