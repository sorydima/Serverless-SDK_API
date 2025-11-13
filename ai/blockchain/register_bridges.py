"""Startup helper to instantiate and register blockchain bridges for the app.

This is useful for examples and tests where you want to use the adapters
or the real bridge implementations if available.
"""
from ai.blockchain.registry import register_bridge

try:
    from ai.blockchain.polkadot_adapter import PolkadotAdapter
except Exception:
    PolkadotAdapter = None

try:
    from ai.blockchain.ton_bridge import TONBridge
except Exception:
    TONBridge = None

try:
    from ai.blockchain.ethereum_bridge import EthereumBridge
except Exception:
    EthereumBridge = None

try:
    from ai.blockchain.rechain_bridge import REChainBridge
except Exception:
    REChainBridge = None


def register_all():
    if PolkadotAdapter is not None:
        pol = PolkadotAdapter()
        register_bridge('polkadot', pol)

    if TONBridge is not None:
        ton = TONBridge()
        register_bridge('ton', ton)

    if EthereumBridge is not None:
        eth = EthereumBridge()
        register_bridge('ethereum', eth)

    if REChainBridge is not None:
        rc = REChainBridge()
        register_bridge('rechain', rc)

    return list(register_bridge.__module__)


if __name__ == '__main__':
    print('Registering bridges...')
    register_all()
    print('Registered bridges:', __import__('ai.blockchain.registry').ai.blockchain.registry.list_bridges() if False else 'see registry')
