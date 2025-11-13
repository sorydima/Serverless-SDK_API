import asyncio
from ai.blockchain.polkadot_adapter import PolkadotAdapter


async def _run_test():
    p = PolkadotAdapter()
    ok = await p.connect()
    assert ok
    res = await p.record_message_hash('m1', 'test', {'a': 1}, metadata={'x': 1})
    assert res
    stats = p.get_stats()
    assert 'Polkadot' in stats.get('network', '') or 'Polkadot' in stats.get('endpoint', '') or 'mock' in stats.get('network', '')
    await p.disconnect()


def test_polkadot_adapter():
    asyncio.run(_run_test())
