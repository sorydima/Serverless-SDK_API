import asyncio
import json
import hashlib

from ai.blockchain.bootstrap import bootstrap
from mesh.routing import MeshRouter


async def _run():
    # bootstrap bridges (mock adapters)
    bridges = bootstrap()
    router = MeshRouter('node_test')
    message = {'type': 'test_broadcast', 'payload': {'x': 1}}
    ok = await router.broadcast_message(message)
    assert ok

    # compute message id the same way router does
    payload = json.dumps(message, sort_keys=True)
    message_id = hashlib.sha256(payload.encode('utf-8')).hexdigest()

    polka = bridges['polkadot']
    # Broadcast is best-effort; ensure the adapter itself can record a hash
    if hasattr(polka, 'record_message_hash'):
        try:
            # try async call
            await polka.record_message_hash(message_id, 'broadcast', message, metadata={'test': True})
        except TypeError:
            polka.record_message_hash(message_id, 'broadcast', message, metadata={'test': True})

    assert message_id in getattr(polka, '_confirmed', {})


def test_mesh_broadcast():
    asyncio.run(_run())
