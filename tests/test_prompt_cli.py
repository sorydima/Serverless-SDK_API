import json
from ai.prompts import cli


def test_format_json_and_yaml_and_env():
    prompts = cli.load_prompts()
    item = prompts[0]
    # JSON
    j = cli.format_prompt_item(item, fmt='json', lang='en')
    parsed = json.loads(j)
    assert parsed['id'] == item['id']
    assert 'prompt' in parsed

    # YAML (basic check: contains id and title)
    y = cli.format_prompt_item(item, fmt='yaml', lang='en')
    assert item['id'] in y
    assert item['title'] in y

    # ENV
    e = cli.format_prompt_item(item, fmt='env', lang='en')
    assert f"PROMPT_ID={item['id']}" in e
    assert 'PROMPT_TEXT=' in e


def test_run_prompt_simulator():
    prompts = cli.load_prompts()
    item = prompts[0]
    resp = cli.run_prompt_by_id(item['id'], model='gpt-sim', lang='en')
    assert isinstance(resp, dict)
    assert 'reply' in resp
    assert resp['prompt'] is not None
