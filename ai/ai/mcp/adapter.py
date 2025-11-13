"""Adapter to integrate internal AI cores with external LLMs via MCP.

Provides a small adapter class that can be used by other modules
to send prompts and receive structured responses.
"""
import asyncio
from typing import Dict, Any, Optional
from .client import MCPClient
from .schema import validate_message


class MCPAdapter:
    def __init__(self, client: Optional[MCPClient] = None):
        self.client = client or MCPClient()

    async def send(self, model: str, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send prompt with optional context and return structured response."""
        context = context or {}
        # Build message and validate against schema contract
        message = {
            'type': 'prompt',
            'model': model,
            'prompt': prompt,
            'metadata': {'context': context}
        }

        # Validate message contract before sending
        validate_message(message)

        # Attach context into metadata and call client
        metadata = message['metadata']
        resp = await self.client.send_prompt(model, prompt, metadata)
        return resp

    async def close(self):
        await self.client.close()


__all__ = ["MCPAdapter"]
