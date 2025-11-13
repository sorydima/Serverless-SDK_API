from ai.blockchain.bootstrap import bootstrap
from ai.blockchain.health import ping_all_sync


def test_ping_all():
    bootstrap()
    res = ping_all_sync()
    assert isinstance(res, dict)
    # Should have our known names
    for expected in ['polkadot', 'ton', 'ethereum', 'rechain']:
        assert expected in res
