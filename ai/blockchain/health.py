"""Health utilities for blockchain bridges.

Provides convenience functions to ping registered bridges and collect their
status for monitoring or smoke tests.
"""
import asyncio
from typing import Dict, Any
from .registry import list_bridges, get_bridge


async def ping_bridge(name: str) -> Dict[str, Any]:
    b = get_bridge(name)
    if not b:
        return {'name': name, 'available': False, 'error': 'not registered'}

    try:
        # Some adapters implement async ping
        if hasattr(b, 'ping'):
            res = b.ping()
            if asyncio.iscoroutine(res):
                ok = await res
            else:
                ok = bool(res)
        else:
            ok = True

        stats = {}
        try:
            stats = b.get_stats()
        except Exception:
            stats = {}

        return {'name': name, 'available': bool(ok), 'stats': stats}

    except Exception as e:
        return {'name': name, 'available': False, 'error': str(e)}


async def ping_all() -> Dict[str, Dict[str, Any]]:
    names = list_bridges()
    results = {}
    for n in names:
        results[n] = await ping_bridge(n)
    return results


def ping_all_sync():
    return asyncio.run(ping_all())


__all__ = ["ping_bridge", "ping_all", "ping_all_sync"]
