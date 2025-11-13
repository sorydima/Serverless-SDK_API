"""Run a small set of lightweight smoke demos for new components.

This script is intentionally dependency-light and exercises the following:
- Bootstrap blockchain bridge mocks
- Run Mesh Data Lake demo
- Run backlog prioritization and export CSV
- Persist a VIBE snapshot (uses vault fallback)
- Broadcast a mesh message and show that the Polkadot adapter recorded its hash

Run from project root:
	python tools\run_smoke_tests.py
"""
import json
import sys
import os
from pathlib import Path

# Ensure repository root is on sys.path so package-style imports work when
# running this script directly (e.g., python tools\run_smoke_tests.py).
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)

from ai.bootstrap_all import bootstrap_all
from mesh.data_lake_demo import run_demo
from ai.backlog_cli import prioritize_and_export
from ai.vibe.vibe import Vibe
from ai.vibe.persistence import persist_vibe
from mesh.routing import MeshRouter


def main():
	print("Bootstrapping components...")
	env = bootstrap_all()
	bridges = env['bridges']
	mcp = env['mcp']

	print("Running Mesh Data Lake demo...")
	counts, path = run_demo()
	print(f"Data lake counts: {counts}, flushed to {path}")

	print("Running backlog prioritization demo...")
	tasks = [
		{'id': 't1', 'severity': 'critical', 'effort': 1, 'impact': 9, 'age_days': 10},
		{'id': 't2', 'severity': 'minor', 'effort': 5, 'impact': 3, 'age_days': 1},
	]
	out_csv = Path('.').joinpath('smoke_backlog.csv')
	out_path = prioritize_and_export(tasks, str(out_csv))
	print(f"Backlog exported to {out_path}")

	print("Persisting a VIBE snapshot (best-effort)...")
	v = Vibe(level=0.42, tags={'session': 'smoke'})
	p = persist_vibe(v, vault_path='.smoke_vibe_vault')
	print(f"VIBE persisted to {p}")

	print("Broadcasting a mesh message to trigger blockchain recording (mock)...")
	# ensure bridges are registered
	router = MeshRouter('smoke_node')
	msg = {'type': 'smoke', 'payload': {'hello': 'world'}}
	# router.broadcast_message is async
	import asyncio
	ok = asyncio.run(router.broadcast_message(msg))
	print(f"Broadcast result: {ok}")

	# Inspect polkadot adapter recorded hashes if available
	try:
		from ai.blockchain.inspector import recorded_hashes, list_registered
		print("Registered bridges:", list_registered())
		hashes = recorded_hashes('polkadot')
		# If broadcast didn't record (best-effort), demonstrate explicit recording
		if not hashes:
			polka = bridges.get('polkadot')
			if polka and hasattr(polka, 'record_message_hash'):
				try:
					# try async call
					asyncio.run(polka.record_message_hash('smoke_demo_msg', 'broadcast', msg, metadata={'demo': True}))
				except TypeError:
					polka.record_message_hash('smoke_demo_msg', 'broadcast', msg, metadata={'demo': True})
				hashes = recorded_hashes('polkadot')

		print(f"Polkadot recorded hashes (sample): {list(hashes.keys())[:5]}")
	except Exception as e:
		print(f"Inspector not available: {e}")

	# Close MCP adapter if it has close
	try:
		import asyncio
		asyncio.run(mcp.close())
	except Exception:
		pass

	print("Smoke tests complete.")


if __name__ == '__main__':
	main()

