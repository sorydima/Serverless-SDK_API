from ai.vibe.vibe import Vibe
from ai.vibe.persistence import persist_vibe
from pathlib import Path


def test_persist_vibe_fallback():
    v = Vibe(level=0.5, tags={'x': 1})
    path = persist_vibe(v, vault_path='.test_vibe_vault', password='pw')
    assert isinstance(path, str)
    # If fallback to file, file should exist
    if not path.startswith('vault:'):
        assert Path(path).exists()
