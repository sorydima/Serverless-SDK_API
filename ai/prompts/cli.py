"""CLI for prompt library: list prompts, format outputs (json/yaml/env), and run a prompt via MCP shim."""
import argparse
import json
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

PROMPT_FILE = Path(__file__).parent / 'ai_quantum_mesh_prompts.json'


def load_prompts(path: Path = PROMPT_FILE):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def _dict_to_simple_yaml(obj, indent: int = 0) -> str:
    # Minimal YAML serializer for simple structures (dicts, lists, primitives)
    pad = '  ' * indent
    out_lines = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                out_lines.append(f"{pad}{k}:")
                out_lines.append(_dict_to_simple_yaml(v, indent + 1))
            else:
                out_lines.append(f"{pad}{k}: {v}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                out_lines.append(f"{pad}-")
                out_lines.append(_dict_to_simple_yaml(item, indent + 1))
            else:
                out_lines.append(f"{pad}- {item}")
    else:
        out_lines.append(f"{pad}{obj}")
    return '\n'.join(out_lines)


def format_prompt_item(item: Dict[str, Any], fmt: str = 'pretty', lang: Optional[str] = None) -> str:
    # choose prompt text by language if available
    text = None
    if lang:
        # check translations
        translations = item.get('translations', {}) or {}
        text = translations.get(lang)
    if text is None:
        # fallback to main prompt text
        text = item.get('prompt')

    out = {
        'id': item.get('id'),
        'title': item.get('title'),
        'lang': lang or item.get('lang'),
        'prompt': text,
        'notes': item.get('notes')
    }

    if fmt == 'json':
        return json.dumps(out, ensure_ascii=False, indent=2)
    if fmt == 'yaml':
        return _dict_to_simple_yaml(out)
    if fmt == 'env':
        # Simple ENV template
        lines = []
        lines.append(f"PROMPT_ID={out['id']}")
        lines.append(f"PROMPT_TITLE={out['title']}")
        lines.append(f"PROMPT_LANG={out['lang']}")
        # Preserve newlines in PROMPT_TEXT by wrapping in quotes
        safe = out['prompt'].replace('"', '\\"') if out['prompt'] else ''
        lines.append(f"PROMPT_TEXT=\"{safe}\"")
        if out.get('notes'):
            notes = out['notes'].replace('\n', ' ')
            lines.append(f"PROMPT_NOTES={notes}")
        return '\n'.join(lines)

    # pretty (default)
    pretty = f"[{out['id']}] {out['title']} ({out['lang']})\n{out['prompt']}\n"
    if out.get('notes'):
        pretty += f"  -> {out['notes']}\n"
    return pretty


async def _send_prompt_async(model: str, prompt: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    # Lazy import to avoid heavy deps during CLI import
    try:
        from ai.ai.mcp.client import MCPClient
    except Exception as e:
        raise RuntimeError(f"Failed to import MCPClient: {e}")

    client = MCPClient()
    try:
        resp = await client.send_prompt(model, prompt, metadata or {})
        return resp
    finally:
        try:
            await client.close()
        except Exception:
            pass


def run_prompt_by_id(prompt_id: str, model: str = 'gpt-sim', lang: Optional[str] = None) -> Dict[str, Any]:
    prompts = load_prompts()
    item = next((p for p in prompts if p.get('id') == prompt_id), None)
    if item is None:
        raise KeyError(f"Prompt id not found: {prompt_id}")
    # choose text
    text = None
    if lang:
        text = (item.get('translations') or {}).get(lang)
    if text is None:
        text = item.get('prompt')

    return asyncio.run(_send_prompt_async(model, text, metadata={'prompt_id': prompt_id}))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Prompt library CLI')
    parser.add_argument('--format', choices=['pretty', 'json', 'yaml', 'env'], default='pretty')
    parser.add_argument('--id', help='Prompt id to show (default: list all)')
    parser.add_argument('--lang', help='Language code to prefer for prompt text (e.g., en)')
    parser.add_argument('--run', action='store_true', help='Run the prompt via local MCP simulator and print the reply')
    parser.add_argument('--generate', action='store_true', help='Generate RFC and code skeleton files for the prompt')
    parser.add_argument('--out-dir', default='.', help='Output directory for generated files')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing generated files')
    parser.add_argument('--model', default='gpt-sim', help='Model name to send to MCP')
    args = parser.parse_args(argv)

    if not PROMPT_FILE.exists():
        print(f"Prompt file not found: {PROMPT_FILE}")
        return 2

    prompts = load_prompts()

    if args.id:
        item = next((p for p in prompts if p.get('id') == args.id), None)
        if item is None:
            print(f"Prompt id not found: {args.id}")
            return 3
        if args.generate:
            # generate files using generator
            try:
                from ai.prompts.generator import generate_files
                created = generate_files(args.id, args.out_dir, use_mcp=not getattr(args, 'no_mcp', False), overwrite=args.overwrite)
                for p in created:
                    print(f"Created: {p}")
                return 0
            except FileExistsError as e:
                print(str(e))
                return 4
            except Exception as e:
                print(f"Generation failed: {e}")
                return 5
        if args.run:
            resp = run_prompt_by_id(args.id, model=args.model, lang=args.lang)
            print(json.dumps(resp, ensure_ascii=False, indent=2))
            return 0
        print(format_prompt_item(item, fmt=args.format, lang=args.lang))
        return 0

    # list all
    for p in prompts:
        print(format_prompt_item(p, fmt=args.format, lang=args.lang))
    return 0


if __name__ == '__main__':
    sys.exit(main())
