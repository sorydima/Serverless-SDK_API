import time
from mesh.multicast_service import MulticastDiscoveryService


def test_multicast_basic(tmp_path):
    svc = MulticastDiscoveryService(port=9998)
    svc.start()
    try:
        svc.broadcast({'id': 'testnode', 'addr': '127.0.0.1'})
        # give some time for loopback
        time.sleep(0.2)
        topo = svc.get_topology(stale_after=10)
        assert 'testnode' in topo
    finally:
        svc.stop()
