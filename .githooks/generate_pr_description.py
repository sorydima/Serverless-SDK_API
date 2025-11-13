"""Generate a draft PR / commit message using the prompt library.

Usage (git prepare-commit-msg hook):
  python .githooks/generate_pr_description.py <commit-msg-file> [prompt_id]

Behavior:
- If the commit message file is empty, this script will prepend a generated
  description created from the selected prompt.
- Default prompt id: 'system_refactor'

Note: enable hooks locally with:
  git config core.hooksPath .githooks
"""
import sys
import os
import json
from pathlib import Path

PROMPT_FILE = Path(__file__).parent.parent / 'ai' / 'prompts' / 'ai_quantum_mesh_prompts.json'


def load_prompts():
    with PROMPT_FILE.open('r', encoding='utf-8') as f:
        return json.load(f)


def build_message(prompt_item, lang: str = 'en'):
    # prefer translation
    text = None
    if prompt_item.get('translations'):
        text = prompt_item['translations'].get(lang)
    if text is None:
        text = prompt_item.get('prompt')

    title = prompt_item.get('title')
    lines = []
    lines.append(f"{title}")
    lines.append("")
    lines.append(text)
    notes = prompt_item.get('notes')
    if notes:
        lines.append("")
        lines.append(f"Notes: {notes}")
    return '\n'.join(lines)


def generate_with_mcp(prompt_item, model: str = 'gpt-sim', mcp_host: str = None):
    """Optionally call MCP shim to produce dynamic description. Falls back to static text."""
    # prefer translation or prompt text
    text = None
    if prompt_item.get('translations'):
        text = prompt_item['translations'].get('en')
    if text is None:
        text = prompt_item.get('prompt')

    # Try to call local MCP client if available or configured
    try:
        # Lazy import to avoid heavy deps during hook execution
        from ai.ai.mcp.client import MCPClient
    except Exception:
        return build_message(prompt_item, lang='en')

    try:
        client = MCPClient(host=mcp_host) if mcp_host else MCPClient()
        import asyncio
        resp = asyncio.run(client.send_prompt(model, text, metadata={'source': 'generate_pr_description'}))
        # Prefer reply if present
        reply = resp.get('reply') if isinstance(resp, dict) else None
        if reply:
            title = prompt_item.get('title')
            return f"{title}\n\n{reply}\n"
    except Exception:
        # ignore MCP failures and fallback
        pass

    return build_message(prompt_item, lang='en')


def main(argv):
    if len(argv) < 2:
        print("Usage: generate_pr_description.py <commit-msg-file> [prompt_id]")
        return 2

    commit_file = Path(argv[1])
    prompt_id = argv[2] if len(argv) > 2 else None

    prompts = load_prompts()
    item = None
    if prompt_id:
        item = next((p for p in prompts if p.get('id') == prompt_id), None)
    if item is None:
        # fallback to first matching id or default
        item = next((p for p in prompts if p.get('id') == 'system_refactor'), prompts[0])

    # If environment variable USE_MCP is set to a truthy value, attempt dynamic generation
    use_mcp = True if (os.environ.get('USE_MCP') or os.environ.get('MCP_HOST')) else False
    mcp_host = os.environ.get('MCP_HOST')
    model = os.environ.get('MCP_MODEL', 'gpt-sim')

    if use_mcp:
        try:
            msg = generate_with_mcp(item, model=model, mcp_host=mcp_host)
        except Exception:
            msg = build_message(item, lang='en')
    else:
        msg = build_message(item, lang='en')

    # Read existing commit message
    orig = ''
    if commit_file.exists():
        orig = commit_file.read_text(encoding='utf-8')

    # If there's already content, do not override; only prepend if empty or small
    if orig.strip():
        # don't overwrite - append suggestion at the end separated by marker
        out = orig + '\n\n# Suggested PR description:\n' + msg + '\n'
    else:
        out = msg + '\n'

    commit_file.write_text(out, encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
