"""Persist VIBE snapshots into the Web5 vault or fallback to JSON file.

This helper stores a Vibe snapshot using the Web5DataVault when available.
If the vault dependency isn't available, it writes a small JSON file
into the specified path as fallback.
"""
import json
from pathlib import Path
from typing import Dict, Any

try:
    from ai.vibe.vibe import Vibe
except Exception:
    # If Vibe isn't importable for some reason, define a light placeholder
    from dataclasses import dataclass

    @dataclass
    class Vibe:
        level: float
        tags: Dict[str, Any]
        timestamp: float = None


def persist_vibe(vibe: Vibe, vault_path: str = '.vibe_vault', password: str = 'changeit') -> str:
    """Try to persist the Vibe snapshot to Web5DataVault; fallback to JSON file.

    Returns the path where the snapshot was stored.
    """
    try:
        from ai.blockchain.web5.vault import Web5DataVault

        vault = Web5DataVault(vault_path, password)
        # store as routing/state snapshot
        import asyncio
        loop = asyncio.get_event_loop()
        entry_id = loop.run_until_complete(vault.store_data('vibe_snapshot', vibe.to_dict(), metadata={'source': 'vibe'}, owner_did=None))
        return f'vault:{entry_id}'

    except Exception:
        # Fallback: store JSON file
        p = Path(vault_path)
        p.mkdir(parents=True, exist_ok=True)
        fname = p / f'vibe_{int(vibe.timestamp or 0)}.json'
        with open(fname, 'w', encoding='utf-8') as f:
            json.dump(vibe.to_dict(), f, indent=2)
        return str(fname)


__all__ = ["persist_vibe"]
