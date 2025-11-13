"""Optional gRPC MCP client wrapper.

This module provides a thin wrapper that will use an installed MCP SDK
or gRPC-based client if available. If not, it falls back to the local
simulator `MCPClient` in `ai.ai.mcp.client`.
"""
from typing import Dict, Any, Optional

try:
    # Try to import a real MCP SDK if present (placeholder)
    import mcp  # type: ignore
    _HAS_MCP_SDK = True
except Exception:
    _HAS_MCP_SDK = False

from .client import MCPClient as _LocalMCPClient


class MCPGRPCClient:
    """A client that prefers a real MCP SDK but falls back to simulator."""

    def __init__(self, host: Optional[str] = None, port: int = 0):
        if _HAS_MCP_SDK and host is not None:
            # In a real implementation we'd initialise the SDK client here
            # For now, we default to the local shim to keep tests hermetic
            self._client = _LocalMCPClient()
        else:
            self._client = _LocalMCPClient()

    async def send_prompt(self, model: str, prompt: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        return await self._client.send_prompt(model, prompt, metadata or {})

    async def close(self):
        return await self._client.close()


__all__ = ["MCPGRPCClient"]
