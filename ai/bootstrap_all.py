"""Top-level bootstrap for app components used by demos/tests.

This will initialize blockchain bridges and (optionally) other
components and return them for programmatic use.
"""
from ai.blockchain.bootstrap import bootstrap as bootstrap_blockchain
from ai.ai.mcp.adapter import MCPAdapter


def bootstrap_all():
    bridges = bootstrap_blockchain()
    mcp = MCPAdapter()
    return {'bridges': bridges, 'mcp': mcp}


__all__ = ['bootstrap_all']
