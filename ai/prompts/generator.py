"""Prompt-to-RFC generator that can use the MCP shim to expand prompts into design docs.

Usage:
    from ai.prompts.generator import generate_rfc
    rfc_text = generate_rfc('multicast_discovery')

The generator prefers to call the local MCP simulator (MCPClient) if available
and falls back to a template-based fill.
"""
import json
from pathlib import Path
from typing import Optional, List

TEMPLATE = Path(__file__).parent / 'templates' / 'rfc_template.md'
PROMPTS = Path(__file__).parent / 'ai_quantum_mesh_prompts.json'


def _load_prompt(prompt_id: str):
    data = json.loads(PROMPTS.read_text(encoding='utf-8'))
    item = next((p for p in data if p.get('id') == prompt_id), None)
    return item


def _fill_template(title: str, summary: str) -> str:
    tmpl = TEMPLATE.read_text(encoding='utf-8')
    return tmpl.format(title=title, summary=summary)


def generate_rfc(prompt_id: str, use_mcp: bool = True, model: str = 'gpt-sim', lang: str = 'en') -> str:
    item = _load_prompt(prompt_id)
    if not item:
        raise KeyError(f"Prompt {prompt_id} not found")

    # choose text
    text = None
    if lang and item.get('translations'):
        text = item['translations'].get(lang)
    if text is None:
        text = item.get('prompt')

    # Attempt MCP expansion
    if use_mcp:
        try:
            from ai.ai.mcp.client import MCPClient
            import asyncio
            client = MCPClient()
            resp = asyncio.run(client.send_prompt(model, f"Expand into RFC: {text}", metadata={'prompt_id': prompt_id}))
            # Use the reply if available
            if isinstance(resp, dict) and resp.get('reply'):
                return _fill_template(item.get('title'), resp.get('reply'))
        except Exception:
            pass

    # Fallback: small summary + template
    summary = f"Prompt: {text}\n\nNotes: {item.get('notes', '')}"
    return _fill_template(item.get('title'), summary)


def generate_files(prompt_id: str, out_dir: str | Path, use_mcp: bool = True, overwrite: bool = False) -> List[Path]:
    """Generate an RFC and optional code skeleton files for a prompt.

    Returns list of created file Paths.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # generate RFC text
    rfc_text = generate_rfc(prompt_id, use_mcp=use_mcp)
    rfc_path = out / f"{prompt_id}.md"
    if rfc_path.exists() and not overwrite:
        raise FileExistsError(f"RFC already exists: {rfc_path}")
    rfc_path.write_text(rfc_text, encoding='utf-8')

    created = [rfc_path]

    # Map prompt ids to code skeleton templates
    skeleton_dir = Path(__file__).parent / 'templates' / 'code_skeletons'
    mapping = {
        'multicast_discovery': 'multicast_service.py.tmpl',
        'bluetooth_mesh': 'ble_mesh_service.py.tmpl',
        'mesh_voting_app': 'mesh_voting_app.py.tmpl',
        'wifi_direct_mesh': 'wifi_direct_service.py.tmpl',
    }

    tmpl_name = mapping.get(prompt_id)
    if tmpl_name:
        tmpl_path = skeleton_dir / tmpl_name
        if tmpl_path.exists():
            target_name = tmpl_path.name.replace('.tmpl', '')
            target_path = out / target_name
            if target_path.exists() and not overwrite:
                raise FileExistsError(f"Target exists: {target_path}")
            # simple templating: replace {prompt_id} and {title}
            item = _load_prompt(prompt_id)
            title = item.get('title') if item else prompt_id
            content = tmpl_path.read_text(encoding='utf-8')
            content = content.replace('{prompt_id}', prompt_id).replace('{title}', title)
            target_path.write_text(content, encoding='utf-8')
            created.append(target_path)

    return created


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generate RFC from prompt')
    parser.add_argument('prompt_id')
    parser.add_argument('--no-mcp', dest='use_mcp', action='store_false')
    args = parser.parse_args()
    print(generate_rfc(args.prompt_id, use_mcp=args.use_mcp))
