# Fix Templates

Templates to use when auto-fixing or manually resolving lint findings.

---

## Rule 6 — Installation section (README.md)

When fixing a missing or incomplete Installation section, use this template (replace `{owner}/{repo}` with the actual GitHub slug):

````markdown
## Installation

### Recommended: `npx skills`

```bash
npx skills add {owner}/{repo}
```

### Manual installation

Copy the skill directory to your agent's skill folder:

| Agent | Directory |
|-------|-----------|
| Claude Code | `~/.claude/skills/` |
| Cursor | `.cursor/skills/` |
| Gemini CLI | `.gemini/skills/` |
| Amp | `.amp/skills/` |
| Roo Code | `.roo/skills/` |
| Copilot | `.github/skills/` |

### As a CLI tool

```bash
uv tool install git+https://github.com/{owner}/{repo}
```
````

---

## Rule 7 — Usage section (README.md)

When fixing a missing or incomplete Usage section, use this template:

````markdown
## Usage

After installing, try these prompts with your agent:

- `<starter prompt 1>`
- `<starter prompt 2>`
- `<starter prompt 3>`

### CLI

You can also run the script directly:

```bash
skill-lint check .                            # Lint repo-root skill
skill-lint check ./my-skill                   # Lint a specific directory
skill-lint check ./my-skill --fix             # Auto-fix fixable issues
skill-lint check ./my-skill --format json     # JSON output for CI
```
````
