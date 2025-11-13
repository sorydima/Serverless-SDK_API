"""Simple Mesh Data Lake: ingestion and lightweight analytics.

This is a minimal, local implementation intended as a starting point.
"""
from typing import Any, Dict, List
import json
from datetime import datetime
from pathlib import Path


class MeshDataLake:
    def __init__(self, storage_path: str = ".mesh_data_lake"):
        self.storage = Path(storage_path)
        self.storage.mkdir(parents=True, exist_ok=True)
        self._items: List[Dict[str, Any]] = []

    def ingest(self, item: Dict[str, Any]):
        item_copy = dict(item)
        item_copy.setdefault('ingested_at', datetime.now().isoformat())
        self._items.append(item_copy)

    def flush(self, filename: str = None) -> str:
        filename = filename or f"data_{datetime.now().timestamp()}.json"
        path = self.storage / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._items, f, indent=2)
        return str(path)

    def count_by_type(self, key: str = 'type'):
        counts = {}
        for it in self._items:
            k = it.get(key, 'unknown')
            counts[k] = counts.get(k, 0) + 1
        return counts

    def clear(self):
        self._items.clear()


__all__ = ["MeshDataLake"]
