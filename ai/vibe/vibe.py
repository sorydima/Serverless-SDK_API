"""VIBE context objects and serializers for cross-node transfer.

VIBE is a lightweight context payload representing node 'mood'/state.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any
from datetime import datetime


@dataclass
class Vibe:
    level: float  # -1.0 .. 1.0
    tags: Dict[str, Any]
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().timestamp()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Vibe':
        return cls(level=data.get('level', 0.0), tags=data.get('tags', {}), timestamp=data.get('timestamp'))


__all__ = ["Vibe"]
