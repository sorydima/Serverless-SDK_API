import asyncio
from ai.blockchain.ton_bridge import TONBridge
from ai.blockchain.ethereum_bridge import EthereumBridge
from ai.blockchain.rechain_bridge import REChainBridge


async def _run_test():
    t = TONBridge()
    e = EthereumBridge()
    r = REChainBridge()

    assert await t.connect()
    assert await e.connect()
    assert await r.connect()

    assert await t.ping()
    assert await e.ping()
    assert await r.ping()

    await t.disconnect()
    await e.disconnect()
    await r.disconnect()


def test_bridges():
    asyncio.run(_run_test())
