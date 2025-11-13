Git hooks for this repository

This directory contains a small prepare-commit-msg hook that generates a draft
commit/PR description from the prompt library located at `ai/prompts`.

Install locally:

1. Enable the repository hooks directory:

```bash
git config core.hooksPath .githooks
```

2. Make the prepare-commit-msg script executable (on Unix/macOS):

```bash
chmod +x .githooks/prepare-commit-msg
```

Usage

- When creating a commit, the hook will populate the commit message with the
  prompt-generated content if the commit message is empty. If the message
  already contains text, the suggested description will be appended as a
  comment block.

Customization

- To select another prompt id, set the second hook argument. Example (manual):

```bash
.git/hooks/prepare-commit-msg <commit-msg-file> feature_request
```

Notes

- On Windows, enable hooks by setting `core.hooksPath` as above. Ensure the
  Python interpreter is available on PATH so the hook can run the generator.
- You can modify `.githooks/generate_pr_description.py` to call the MCP shim
  to generate dynamic descriptions (it currently uses static prompt text).
