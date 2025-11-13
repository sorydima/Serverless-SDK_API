"""Small CLI to run backlog prioritization and export CSV.

Usage (programmatic):
    from ai.backlog_cli import prioritize_and_export
    prioritize_and_export(tasks, 'out.csv')
"""
import csv
from typing import List, Dict, Any
from .backlog_intel import prioritize


def prioritize_and_export(tasks: List[Dict[str, Any]], out_path: str) -> str:
    prioritized = prioritize(tasks)
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'score', 'severity', 'effort', 'impact', 'age_days'])
        for t in prioritized:
            writer.writerow([t.get('id'), t.get('score'), t.get('severity'), t.get('effort'), t.get('impact'), t.get('age_days')])
    return out_path


__all__ = ["prioritize_and_export"]
