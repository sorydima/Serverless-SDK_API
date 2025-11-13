"""Simple MCP message contract and validator.

This file contains a lightweight JSON-like schema and a validator used
by adapters to ensure outgoing messages meet minimal expectations.
"""
from typing import Dict, Any

MESSAGE_SCHEMA = {
    'type': str,          # e.g., 'prompt', 'config', 'control'
    'model': str,         # model identifier
    'prompt': str,        # prompt text
    'metadata': dict      # arbitrary metadata
}


def validate_message(msg: Dict[str, Any]) -> bool:
    """Very small validator: checks required keys and types.

    Returns True if message appears valid; raises ValueError otherwise.
    """
    if not isinstance(msg, dict):
        raise ValueError("MCP message must be a dict")

    for key, t in MESSAGE_SCHEMA.items():
        if key not in msg:
            raise ValueError(f"Missing required key: {key}")
        if not isinstance(msg[key], t):
            raise ValueError(f"Field '{key}' must be of type {t.__name__}")

    return True


__all__ = ["MESSAGE_SCHEMA", "validate_message"]
