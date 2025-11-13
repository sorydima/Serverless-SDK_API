import json
from pathlib import Path


def test_prompt_file_exists_and_has_prompts():
    p = Path(__file__).parents[1] / 'ai' / 'prompts' / 'ai_quantum_mesh_prompts.json'
    assert p.exists(), f"Prompt file not found at {p}"
    data = json.loads(p.read_text(encoding='utf-8'))
    assert isinstance(data, list), "Prompt file should contain a JSON array"
    assert len(data) >= 5, "Expected at least 5 prompts in the library"
    # Basic schema checks for first item
    item = data[0]
    assert 'id' in item and 'prompt' in item and 'title' in item and 'lang' in item
