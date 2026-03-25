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
  version: 0.7.0
---

# Agent Skill Linter

Checks agent skills for spec compliance and publishing readiness.

## Triage Workflow

**Target:** the skill directory to lint — current directory (`.`) or a path provided by the user.

### Step 1 — Get the full picture

```bash
uvx --from git+https://github.com/William-Yeh/agent-skill-linter skill-lint check <target>
```

### Step 2 — Fix Errors first

**Rule 1** (SKILL.md spec compliance) blocks publishing. Fix before anything else.

### Step 3 — Auto-fix Warnings

```bash
uvx --from git+https://github.com/William-Yeh/agent-skill-linter skill-lint check <target> --fix
```

For fixable rules without CLI, use the templates in `references/fix-templates.md`.

### Step 4 — Resolve remaining Warnings manually

CSO naming (Rules 11–12), Python invocations (Rule 13) — see the rule table below.

### Step 5 — Address Info items as polish

Content dedup (Rule 8), body length (Rule 9), non-standard dirs (Rule 10).

## What It Checks

| # | Rule | Severity | Auto-fix |
|---|------|----------|----------|
| 1 | SKILL.md spec compliance (via skills-ref) | Error | — |
| 2 | LICENSE exists, Apache-2.0 or MIT, current year | Warning | Yes |
| 3 | `metadata.author` in SKILL.md frontmatter | Warning | Yes |
| 4 | README badges (CI, license, Agent Skills) | Warning | Yes |
| 5 | `.github/workflows/` has CI workflow | Warning | Yes |
| 6 | README has Installation section | Warning | Yes |
| 7 | README has Usage section with starter prompts + CLI subsection | Warning | Partial |
| 8 | Content dedup between README.md and SKILL.md | Info | — |
| 9 | SKILL.md body < 500 lines | Info | — |
| 10 | Non-standard directories flagged | Info | — |
| 11 | CSO: description starts with "Use when..." | Warning | — |
| 12 | CSO: name is action-oriented (gerund preferred) | Info | — |
| 13 | Python invocation consistency (`uv run python` in uv projects) | Warning | — |
| 14 | Progressive disclosure: embedded templates (4-backtick fences) → `references/` | Warning | Yes |
| 15 | Progressive disclosure: reference-tier headings (Troubleshooting, FAQ, Advanced…) → `references/` | Warning | Yes |
| 16 | Progressive disclosure: heavy step sections (>30 lines) → `references/` | Info | — |

## CLI Reference

```bash
skill-lint check .                            # Lint repo-root skill
skill-lint check ./my-skill --fix             # Auto-fix fixable issues
skill-lint check ./my-skill --format json     # JSON output for CI
```

Exit code 1 on errors, 0 otherwise.
