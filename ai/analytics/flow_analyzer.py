"""Simple streaming analyzer for Mesh Data Lake flows.

This analyzer computes basic aggregations and anomaly detection stubs.
"""
from typing import List, Dict, Any


def aggregate_sum(items: List[Dict[str, Any]], key: str = 'value') -> float:
    return sum(float(it.get(key, 0)) for it in items)


def detect_anomalies(items: List[Dict[str, Any]], key: str = 'value', threshold: float = 100.0) -> List[Dict[str, Any]]:
    return [it for it in items if float(it.get(key, 0)) > threshold]


__all__ = ["aggregate_sum", "detect_anomalies"]
