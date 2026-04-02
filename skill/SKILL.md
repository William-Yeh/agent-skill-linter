---
name: agent-skill-linter
description: >
  Use when validating an agent skill for spec compliance and publishing readiness.
metadata:
  author: William Yeh <william.pjyeh@gmail.com>
  license: Apache-2.0
  version: 0.8.0
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

CSO naming (Rules 11–12), Python invocations (Rule 13), description conciseness (Rule 18) — see the rule table below.

### Step 5 — Semantic review: description

Rules 11 and 18 catch structural patterns but not meaning. Read the `description` frontmatter and ask: **does it function purely as a routing signal?**

Flag it if it:
- Enumerates what the skill checks, handles, or supports
- Reads as a feature summary or workflow overview
- Could be trimmed to one clause without losing routing precision

A good description names the trigger condition only. Everything else belongs in the skill body.

### Step 6 — Semantic review: starter prompts

Rule 7 detects whether prompts exist, not whether they're useful. Read the Usage section starter prompts and ask: **do they reflect genuine, distinct trigger scenarios?**

Flag them if they:
- Are vague or generic (e.g. `Use this skill`, `Run the linter`)
- All describe the same scenario with minor wording variation
- Don't reflect the range of contexts a real user would encounter

### Step 7 — Semantic review: content overlap

Rule 8 catches identical lines between SKILL.md and README. Ask: **is the same information conveyed in different words?**

Flag paraphrased repetition that the linter cannot detect. SKILL.md should be agent-focused (triage workflow, rules); README should be human-focused (installation, usage examples).

### Step 8 — Semantic review: progressive disclosure

Rules 15 and 16 use heading keywords and line counts. Ask: **would an agent look up this section reactively rather than read it upfront?**

Flag sections for `references/` if they:
- Are reference material regardless of their heading name (e.g. "Background", "How It Works")
- Are dense or conditional even if under 30 lines

### Step 9 — Address Info items as polish

Content dedup (Rule 8), body length (Rule 9), non-standard dirs (Rule 10), skill isolation (Rule 17).

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
| 8 | Content dedup between README.md and SKILL.md | Info | Step 7 |
| 9 | SKILL.md body < 500 lines | Info | — |
| 10 | Non-standard directories flagged | Info | — |
| 11 | CSO: description starts with "Use when..." | Warning | Step 5 |
| 12 | CSO: name is action-oriented (gerund preferred) | Info | — |
| 13 | Python invocation consistency (`uv run python` in uv projects) | Warning | — |
| 14 | Progressive disclosure: embedded templates (4-backtick fences) → `references/` | Warning | Yes |
| 15 | Progressive disclosure: reference-tier headings (Troubleshooting, FAQ, Advanced…) → `references/` | Warning | Yes + Step 8 |
| 16 | Progressive disclosure: heavy step sections (>30 lines) → `references/` | Info | Step 8 |
| 17 | Skill isolation: SKILL.md at repo root alongside non-skill artifacts | Info | — |
| 18 | CSO: description is a single routing clause (no elaboration labels or multiple sentences) | Warning | Step 5 |

## CLI Reference

```bash
skill-lint check .                            # Lint repo-root skill
skill-lint check ./my-skill --fix             # Auto-fix fixable issues
skill-lint check ./my-skill --format json     # JSON output for CI
```

Exit code 1 on errors, 0 otherwise.
