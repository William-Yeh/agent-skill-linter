---
name: agent-skill-linter
description: >
  Use when publishing an agent skill to GitHub or checking an existing skill
  for spec compliance and readiness. Triggers on: SKILL.md frontmatter
  violations, missing LICENSE, missing README badges, no CI workflow,
  incomplete installation or usage docs.
metadata:
  author: William Yeh <william.pjyeh@gmail.com>
  license: Apache-2.0
  version: 0.5.0
---

# Agent Skill Linter

A linter that checks agent skills for spec compliance and publishing readiness.

## What it checks

1. **SKILL.md spec compliance** — delegates to `skills-ref` for frontmatter validation
2. **LICENSE** — exists, Apache-2.0 or MIT, current year
3. **Author** — `metadata.author` in SKILL.md frontmatter
4. **README badges** — CI, license, Agent Skills badges
5. **CI workflow** — `.github/workflows/` has at least one YAML workflow
6. **Installation section** — README has install instructions with `npx skills` and agent directory table
7. **Usage section** — README has usage examples with starter prompts
8. **Content dedup** — flags heavy overlap between README.md and SKILL.md
9. **Body length** — SKILL.md body under 500 lines
10. **Directory structure** — flags non-standard directories
11. **CSO description** — description starts with "Use when..." (triggering conditions, not workflow summary)
12. **CSO name** — name is action-oriented (gerund preferred over noun forms)
13. **Python invocation consistency** — docs use `uv run python` when project is uv-managed with non-stdlib deps; exceptions for heredoc one-liners using only stdlib

## Running

```bash
skill-lint check ./my-skill          # Lint a skill directory
skill-lint check ./my-skill --fix    # Auto-fix fixable issues
skill-lint check ./my-skill --format json  # JSON output for CI
```

Exit code 1 on errors, 0 otherwise.

## Templates

### Installation section (for README.md)

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
