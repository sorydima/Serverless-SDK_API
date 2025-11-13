# Blockchain Bridges

This folder contains bridge implementations used by the mesh and AI
components to interact with blockchains. There are two operating modes:

1. Production: install the required external libraries (for example,
   `py-substrate-interface` for Polkadot) and configure endpoints/keys.
2. Development/test: the repository includes lightweight mock adapters
   that run entirely in-process for unit tests and local development.

Files of interest:

- `polkadot/bridge.py` - full Polkadot recorder using `py-substrate-interface` (requires that package).
- `bridge_base.py` - abstract `BlockchainBridge` interface used by adapters.
- `ton_bridge.py`, `ethereum_bridge.py`, `rechain_bridge.py` - lightweight mock connectors.
- `polkadot_adapter.py` - adapter that wraps the real Polkadot bridge if available, otherwise provides an in-memory mock.

Enabling real bridges
---------------------
To use the real Polkadot bridge, install dependencies (example):

```powershell
pip install py-substrate-interface
```

Then ensure network endpoint and keypair are configured when instantiating the bridge.

For MCP and other external services, see `ai/ai/mcp/README.md`.
