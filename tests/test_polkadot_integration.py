import os
import pytest


pytestmark = pytest.mark.skipif(
    not (os.environ.get('POLKADOT_ENDPOINT') and os.environ.get('POLKADOT_KEYPAIR')),
    reason='POLKADOT_ENDPOINT and POLKADOT_KEYPAIR not set'
)


def test_polkadot_connect_and_record():
    # This test requires network access and valid credentials. It will only run
    # when POLKADOT_ENDPOINT and POLKADOT_KEYPAIR are provided via CI secrets.
    try:
        from ai.blockchain.polkadot.bridge import PolkadotBridge
    except Exception as e:
        pytest.skip(f'Polkadot bridge import failed: {e}')

    endpoint = os.environ['POLKADOT_ENDPOINT']
    keypair = os.environ['POLKADOT_KEYPAIR']

    bridge = PolkadotBridge(endpoint=endpoint, keypair_uri=keypair)

    # Attempt to connect; this will raise or return False on failure
    import asyncio

    async def run():
        connected = await bridge.connect()
        assert connected
        # Try a lightweight recording (hash of 'test')
        res = await bridge.record_message_hash('int_test_1', 'test', 'hello', metadata={'ci': True})
        assert res is True
        await bridge.disconnect()

    asyncio.run(run())
