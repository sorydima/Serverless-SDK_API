from ai.blockchain.bootstrap import bootstrap
from ai.blockchain.registry import list_bridges, get_bridge


def test_bootstrap_and_registry():
    objs = bootstrap()
    names = list_bridges()
    assert 'polkadot' in names
    assert 'ton' in names
    assert isinstance(get_bridge('polkadot'), object)
