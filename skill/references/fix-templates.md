# Fix Templates

Templates to use when auto-fixing or manually resolving lint findings.

Two-mode coverage: each Rule 6 / Rule 7 entry has a **single-skill** variant
and a **plugin** variant. The auto-fixer picks the right one based on whether
`.claude-plugin/plugin.json` is present at the lint target. When applying
manually, pick the variant that matches the layout you're shipping (see
ADR-0001 in linter docs and ADR-0001 in `narrative-analysis` for layout
distinctions).

---

## Rule 6 — Installation section (README.md)

When fixing a missing or incomplete Installation section, replace
`{owner}/{repo}` with the actual GitHub slug.

### Single-skill variant

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

### Plugin variant

````markdown
## Installation

Install as a Claude Code plugin:

```bash
/plugin install {owner}/{repo}
```

The plugin manifest at `.claude-plugin/plugin.json` declares the bundled
skills; each lands in `~/.claude/plugins/cache/.../skills/<name>/` after
install.

### Local development

```bash
git clone https://github.com/{owner}/{repo}.git
cd {repo}
uv sync --all-groups
```
````

---

## Rule 7 — Usage section (README.md)

When fixing a missing or incomplete Usage section, use the variant that
matches your layout. Both must include 3+ starter prompts and a CLI
subsection (Rule 7 sub-checks 7.1 and 7.2).

### Single-skill variant

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

### Plugin variant

A plugin can host multiple skills, so prompts should reflect the bundled
triggers and any cross-skill workflow. The CLI subsection should mention
both the plugin's shared console scripts (if any) and how skill `scripts/`
are invoked directly via `uv run`.

````markdown
## Usage

After installing the plugin, try these prompts with your agent (each bundled
skill exposes its own trigger):

- `<starter prompt for skill 1>`
- `<starter prompt for skill 2>`
- `<cross-skill or shared-library prompt>`

### CLI

The plugin's shared library exposes a console entry point:

```bash
{plugin-cli-name} <args>            # via `pyproject.toml [project.scripts]`
```

Skill scripts in `skills/<name>/scripts/` are also self-contained via
PEP 723 — invoking them through `uv run` from a fresh environment provisions
deps automatically:

```bash
uv run skills/<skill-name>/scripts/<script>.py [options]
```
````
