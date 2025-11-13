import tempfile
from pathlib import Path
from ai.prompts.generator import generate_files


def test_generate_files_creates_rfc_and_skeleton(tmp_path):
    out = tmp_path / 'out'
    created = generate_files('multicast_discovery', out, use_mcp=False, overwrite=True)
    # Expect at least the RFC and a multicast skeleton or none
    assert any(p.name.endswith('.md') for p in created)
    # if a skeleton exists it should be a .py file
    py_files = [p for p in created if p.suffix == '.py']
    if py_files:
        assert py_files[0].exists()
    # verify rfc content
    rfc = out / 'multicast_discovery.md'
    assert rfc.exists()
    text = rfc.read_text(encoding='utf-8')
    assert '# ' in text
