# agent-skill-linter

[![CI](https://github.com/William-Yeh/agent-skill-linter/actions/workflows/ci.yml/badge.svg)](https://github.com/William-Yeh/agent-skill-linter/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/William-Yeh/agent-skill-linter)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-blue)](https://agentskills.io)

Lint agent skills for spec compliance and publishing readiness. Checks everything needed for a polished GitHub release — SKILL.md frontmatter, LICENSE, badges, CI, docs — with auto-fix for common issues.

## Installation

### Recommended: `npx skills`

```bash
npx skills add William-Yeh/agent-skill-linter
```

### Manual installation

Copy the `skill/` directory to your agent's skill folder as `agent-skill-linter`:

| Agent | Directory |
|-------|-----------|
| Claude Code | `~/.claude/skills/agent-skill-linter/` |
| Cursor | `.cursor/skills/agent-skill-linter/` |
| Gemini CLI | `.gemini/skills/agent-skill-linter/` |
| Amp | `.amp/skills/agent-skill-linter/` |
| Roo Code | `.roo/skills/agent-skill-linter/` |
| Copilot | `.github/skills/agent-skill-linter/` |

## Usage

After installing, try these prompts with your agent:

- `Lint the skill in this directory for publishing readiness`
- `Check ~/projects/my-skill for spec compliance and fix any issues`
- `Triage this skill and tell me what's blocking a GitHub release`

### CLI

Run the script directly from the installed skill directory:

```bash
./scripts/skill-lint.py check ./my-skill          # Lint a skill directory
./scripts/skill-lint.py check .                    # Lint repo-root skill
./scripts/skill-lint.py check ./my-skill --fix    # Auto-fix fixable issues
./scripts/skill-lint.py check ./my-skill --format json  # JSON output for CI
```

Requires [uv](https://docs.astral.sh/uv/). Exit code: 1 if errors, 0 otherwise.

## What Gets Checked

The linter checks ~20 rules across six categories:

- **Spec compliance** — SKILL.md frontmatter, required fields, version (Rule 1, Error)
- **Repo hygiene** — LICENSE, CI workflow, README sections, badges (Rules 2–7)
- **Routing signal quality** — `description` prefix, gerund names (Rule 11, plus semantic Steps 5/6)
- **Progressive disclosure** — body size, reference-tier headings moved to `references/` (Rules 9, 14, 15, plus semantic Step 8)
- **Multi-step workflow quality** — exit conditions, retry caps, observable triggers (semantic Steps 8 and 9)
- **Plugin mode** — manifest validity, script dep declarations (Rules 24, 25, Error)

For the full rule list with severities and auto-fix status, see [`skill/SKILL.md`](skill/SKILL.md#what-it-checks). Semantic rules — judgment-based checks not amenable to static analysis — are documented in [`skill/references/semantic-rules.md`](skill/references/semantic-rules.md) and applied by the agent during Steps 5–9 of the triage workflow.

### Plugin layout

When the lint target contains `.claude-plugin/plugin.json`, the linter switches to plugin mode: validates the manifest, checks each skill's script dependencies, and runs the per-skill rule pack across all `skills/<name>/` directories. Single-skill repos lint as before.
