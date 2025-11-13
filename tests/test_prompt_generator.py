from ai.prompts.generator import generate_rfc


def test_generate_rfc_from_prompt():
    r = generate_rfc('multicast_discovery', use_mcp=True)
    assert 'Multicast' in r or 'multicast' in r.lower()
    assert 'Topology' in r or 'topology' in r.lower()
