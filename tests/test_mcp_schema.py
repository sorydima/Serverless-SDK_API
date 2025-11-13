from ai.ai.mcp.schema import validate_message


def test_validate_message_accepts_valid():
    msg = {
        'type': 'prompt',
        'model': 'gpt-sim',
        'prompt': 'hello',
        'metadata': {'context': {}}
    }
    assert validate_message(msg) is True


def test_validate_message_rejects_invalid():
    bad = {'type': 'prompt', 'model': 123, 'prompt': 'x', 'metadata': {}}
    try:
        validate_message(bad)
        assert False, "Expected ValueError"
    except ValueError:
        assert True
