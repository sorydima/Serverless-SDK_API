AI Quantum Mesh App Ecosystem — Prompt Library

This folder stores a small curated library of system prompts related to the "AI Quantum Mesh" project. The prompts are written in Russian (primary) and include a short "notes" field describing intent.

Files:
- `ai_quantum_mesh_prompts.json` — primary prompt data (JSON array). Each item has: id, title, lang, prompt, notes.
- `cli.py` — small CLI to list prompts (optional, convenience).

Usage examples

Load the JSON from Python:

```py
import json
from pathlib import Path
p = Path(__file__).parent / 'ai_quantum_mesh_prompts.json'
prompts = json.loads(p.read_text(encoding='utf-8'))
for item in prompts:
    print(item['id'], item['prompt'])
```

Contribute

- Add, translate, or expand prompts as separate objects in the JSON file.
- Keep prompts concise and include the language tag.
