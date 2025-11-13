"""Bootstrap and register blockchain bridge instances for the app.

This script creates adapter instances (mock or real) and registers them
in the `ai.blockchain.registry` for other components to look up.
"""
from .registry import register_bridge
from .polkadot_adapter import PolkadotAdapter
from .ton_bridge import TONBridge
from .ethereum_bridge import EthereumBridge
from .rechain_bridge import REChainBridge


def bootstrap():
    polka = PolkadotAdapter()
    ton = TONBridge()
    eth = EthereumBridge()
    re = REChainBridge()

    register_bridge('polkadot', polka)
    register_bridge('ton', ton)
    register_bridge('ethereum', eth)
    register_bridge('rechain', re)

    return {'polkadot': polka, 'ton': ton, 'ethereum': eth, 'rechain': re}


if __name__ == '__main__':
    print(bootstrap())
