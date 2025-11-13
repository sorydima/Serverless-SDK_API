"""Simple inspector to query registered blockchain bridges.

Provides small utilities to list recorded hashes and basic bridge stats.
"""
from typing import Dict, Any, List
from .registry import get_bridge, list_bridges


def list_registered() -> List[str]:
    return list_bridges()


def bridge_stats(name: str) -> Dict[str, Any]:
    b = get_bridge(name)
    if not b:
        return {}
    stats = {}
    try:
        stats = b.get_stats()
    except Exception:
        # Fallback best-effort
        stats = {k: getattr(b, k, None) for k in ['endpoint', 'connected']}
    return stats


def recorded_hashes(name: str):
    b = get_bridge(name)
    if not b:
        return []
    return getattr(b, '_confirmed', {})


__all__ = ["list_registered", "bridge_stats", "recorded_hashes"]
