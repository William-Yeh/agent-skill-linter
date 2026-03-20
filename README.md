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
uv tool install git+https://github.com/William-Yeh/agent-skill-linter
```

## Usage

After installing, try these prompts with your agent:

- `Lint the skill in this repo for publishing readiness`
- `Check my skill for spec compliance and fix any issues`
- `Run skill-lint check . --fix to auto-fix common issues`

### CLI

You can also run the script directly:

```bash
skill-lint check ./my-skill          # Lint a skill directory
skill-lint check .                    # Lint repo-root skill
skill-lint check ./my-skill --fix    # Auto-fix fixable issues
skill-lint check ./my-skill --format json  # JSON output for CI
```

Exit code: 1 if errors, 0 otherwise.

## Lint Rules

| # | Rule | Severity | Fixable |
|---|------|----------|---------|
| 1 | SKILL.md spec compliance (via skills-ref) | Error | No |
| 2 | LICENSE exists, Apache-2.0 or MIT, current year | Warning | Yes |
| 3 | `metadata.author` in SKILL.md frontmatter | Warning | Yes |
| 4 | README badges (CI, license, Agent Skills) | Warning | Yes |
| 5 | `.github/workflows/` has CI workflow | Warning | Yes |
| 6 | README has Installation section | Warning | Yes |
| 7 | README has Usage section | Warning | Yes |
| 7.1 | README Usage section has starter prompt examples | Warning | No |
| 7.2 | README Usage section has CLI usage subsection | Info | No |
| 8 | Content dedup between README.md and SKILL.md | Info | No |
| 9 | SKILL.md body < 500 lines | Info | No |
| 10 | Non-standard dirs flagged | Info | No |
| 11 | CSO: description starts with "Use when..." | Warning | No |
| 12 | CSO: name is action-oriented (gerund preferred) | Info | No |
| 13 | Python invocation consistency (`uv run python` in uv projects) | Warning | No |
