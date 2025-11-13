"""Registry for blockchain bridges so mesh/components can look them up.

Simple global registry to register and retrieve bridge instances by name.
"""
from typing import Dict, Any, Optional

_REGISTRY: Dict[str, Any] = {}


def register_bridge(name: str, bridge) -> None:
    _REGISTRY[name] = bridge


def get_bridge(name: str):
    return _REGISTRY.get(name)


def list_bridges():
    return list(_REGISTRY.keys())


__all__ = ["register_bridge", "get_bridge", "list_bridges"]
