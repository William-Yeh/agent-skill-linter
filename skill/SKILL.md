---
name: agent-skill-linter
description: >
  Use when validating an agent skill for spec compliance and publishing readiness.
metadata:
  author: William Yeh <william.pjyeh@gmail.com>
  license: Apache-2.0
  version: 0.10.0
---

# Agent Skill Linter

Checks agent skills for spec compliance and publishing readiness.

## Triage Workflow

**Target:** the skill directory to lint — current directory (`.`) or a path provided by the user.

### Step 1 — Get the full picture

```bash
./scripts/skill-lint.py check <target>
```

### Step 2 — Fix Errors first

**Rule 1** (SKILL.md spec compliance) blocks publishing. Fix before anything else.

### Step 3 — Auto-fix Warnings

```bash
./scripts/skill-lint.py check <target> --fix
```

For fixable rules without CLI, use the templates in `references/fix-templates.md`.

### Step 4 — Resolve remaining Warnings manually

CSO description prefix (Rule 11), Python invocations (Rule 13), README-tier sections in SKILL.md (Rule 19) — see the rule table below.

### Step 5 — Semantic review: CSO signal

Rule 11 catches structural patterns but not meaning. Read the `description` and `name` frontmatter and ask: **do they function purely as routing signals?**

> See `references/semantic-rules.md` — Rules 12 and 18 for examples.

Flag the description if it:
- Enumerates what the skill checks, handles, or supports
- Reads as a feature summary or workflow overview
- Contains elaboration labels (`Triggers on:`, `Use cases:`, `Checks:`) or multiple sentences
- Could be trimmed to one clause without losing routing precision

Flag the name if it reads as a noun phrase rather than an action — prefer gerunds (`creating-skills`, `processing-pdfs`) over noun forms (`skill-creator`, `pdf-processor`). Short well-known names (`pdf`, `commit`) are fine.

A good description names the trigger condition only. Everything else belongs in the skill body.

### Step 6 — Semantic review: starter prompts

Rule 7 detects whether prompts exist, not whether they're useful. Read the Usage section starter prompts and ask: **do they reflect genuine, distinct trigger scenarios?**

Flag them if they:
- Are vague or generic (e.g. `Use this skill`, `Run the linter`)
- All describe the same scenario with minor wording variation
- Don't reflect the range of contexts a real user would encounter

### Step 7 — Semantic review: content overlap

The linter does not check this. Ask: **is the same information conveyed in different words across SKILL.md and README?**

> See `references/semantic-rules.md` — Rule 8 for examples.

Flag paraphrased repetition. SKILL.md should be agent-focused (triage workflow, rules); README should be human-focused (installation, usage examples).

### Step 8 — Semantic review: progressive disclosure

Rule 15 flags known reference-tier keywords, but not all reactive content has a recognizable heading. Ask: **would an agent look up this section reactively rather than read it upfront?**

> See `references/semantic-rules.md` — Rule 16 for examples.

Flag sections for `references/` if they:
- Are reference material regardless of their heading name (e.g. "Background", "How It Works")
- Are dense or conditional — even if short and not caught by Rule 15
- Are step-specific detail blocks that bulk up the main workflow without being needed upfront

### Step 9 — Address Info items as polish

Body length (Rule 9), non-standard dirs (Rule 10), skill isolation (Rule 17).

## What It Checks

| # | Rule | Severity | Auto-fix |
|---|------|----------|----------|
| 1 | SKILL.md spec compliance (via skills-ref) | Error | — |
| 2 | LICENSE exists, Apache-2.0 or MIT, current year | Warning | Partial |
| 3 | `metadata.author` in SKILL.md frontmatter | Warning | Yes |
| 4 | README badges (CI, license, Agent Skills) | Warning | Yes |
| 5 | `.github/workflows/` has CI workflow | Warning | Yes |
| 6 | README has Installation section | Warning | Yes |
| 7 | README has Usage section with starter prompts + CLI subsection | Warning | Partial + Step 6 |
| 9 | SKILL.md body < 500 lines | Info | — |
| 10 | Non-standard directories flagged | Info | — |
| 11 | CSO: description starts with "Use when..." | Warning | Step 5 |
| 13 | Python invocation consistency (`uv run python` in uv projects) | Warning | — |
| 14 | Progressive disclosure: embedded templates (4-backtick fences) → `references/` | Warning | Yes |
| 15 | Progressive disclosure: reference-tier headings (Troubleshooting, FAQ, Advanced…) → `references/` | Warning | Yes + Step 8 |
| 17 | Skill isolation: SKILL.md at repo root alongside non-skill artifacts | Info | — |
| 19 | Division of labor: README-tier sections (Installation, Features, Getting Started…) in SKILL.md | Warning | — |
| 20 | Triage workflow has 3+ steps but no semantic review step (e.g. "Ask: does it…") | Info | Step 5–8 |
| 21 | Python entry-point scripts in `scripts/` lack PEP 723 inline dependency metadata | Warning | — |

## CLI Reference

```bash
./scripts/skill-lint.py check .                            # Lint repo-root skill
./scripts/skill-lint.py check ./my-skill --fix             # Auto-fix fixable issues
./scripts/skill-lint.py check ./my-skill --format json     # JSON output for CI
```

Exit code 1 on errors, 0 otherwise.
