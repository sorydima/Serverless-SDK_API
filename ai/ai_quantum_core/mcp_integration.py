"""Small helper to wire the QuantumBridge to MCP adapter.

QuantumBridge can import and use MCPAdapter.send_prompt to forward
AI-related prompts to external LLMs via MCP.
"""
from typing import Dict, Any
from ai.ai.mcp.adapter import MCPAdapter


_adapter = MCPAdapter()


async def send_prompt_to_llm(model: str, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    return await _adapter.send(model, prompt, context or {})


async def close_adapter():
    await _adapter.close()
