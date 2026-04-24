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

## Lint Rules

| # | Rule | Severity | Fixable |
|---|------|----------|---------|
| 1 | SKILL.md spec compliance (via skills-ref) | Error | No |
| 2 | LICENSE exists, Apache-2.0 or MIT, current year | Warning | Partial |
| 3 | `metadata.author` in SKILL.md frontmatter | Warning | Yes |
| 4 | README badges (CI, license, Agent Skills) | Warning | Yes |
| 5 | `.github/workflows/` has CI workflow | Warning | Yes |
| 6 | README has Installation section | Warning | Yes |
| 7 | README has Usage section | Warning | Yes |
| 7.1 | README Usage section has starter prompt examples | Warning | No |
| 7.2 | README Usage section has CLI usage subsection | Info | No |
| 9 | SKILL.md body < 500 lines | Info | No |
| 10 | Non-standard dirs flagged | Info | No |
| 11 | CSO: description starts with "Use when..." | Warning | No |
| 13 | Python invocation consistency (`uv run python` in uv projects) | Warning | No |
| 14 | Progressive disclosure: embedded templates (4-backtick fences) → `references/` | Warning | Yes |
| 15 | Progressive disclosure: reference-tier section headings (Troubleshooting, FAQ, Advanced…) → `references/` | Warning | Yes |
| 17 | Skill isolation: SKILL.md at repo root alongside non-skill artifacts (README, LICENSE, src/, tests/, …) | Info | No |
| 19 | Division of labor: README-tier sections (Installation, Features, Getting Started…) in SKILL.md | Warning | No |
| 20 | Triage workflow has 3+ steps but no semantic review step (e.g. "Ask: does it…") | Info | No |
| 21 | Python entry-point scripts in `scripts/` lack PEP 723 inline dependency metadata | Warning | No |

Rules 8, 12, 16, 18, 22, and 23 were intentionally removed from automated checking — their mechanical proxies produced unreliable results. Equivalent guidance lives in the agent triage workflow (SKILL.md Steps 5–9) and `references/semantic-rules.md`.
