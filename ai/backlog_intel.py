"""Backlog intelligence: scoring and auto-prioritization stub.

This module provides a simple rule-based scoring function and a
CLI-friendly prioritization function used in tests and demos.
"""
from typing import List, Dict, Any


def score_task(task: Dict[str, Any]) -> float:
    """Return a priority score between 0.0 and 1.0."""
    score = 0.0
    # Basic heuristics
    if task.get('severity') == 'critical':
        score += 0.5
    if task.get('effort', 1) <= 2:
        score += 0.2
    if task.get('impact', 0) >= 8:
        score += 0.2
    # Age: older tasks get small boost
    age = task.get('age_days', 0)
    score += min(0.1, age * 0.01)
    return min(1.0, score)


def prioritize(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return tasks sorted by decreasing score, attach score field."""
    for t in tasks:
        t['score'] = score_task(t)
    return sorted(tasks, key=lambda x: x['score'], reverse=True)


__all__ = ["score_task", "prioritize"]
