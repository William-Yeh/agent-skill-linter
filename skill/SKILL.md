---
name: agent-skill-linter
description: >
  Use when validating an agent skill for spec compliance and publishing readiness.
metadata:
  author: William Yeh <william.pjyeh@gmail.com>
  license: Apache-2.0
  version: 0.15.1
---

# Agent Skill Linter

Checks agent skills for spec compliance and publishing readiness.

## Expected Layouts

Two layouts are supported, auto-detected by presence of `.claude-plugin/plugin.json` at the target:

- **Single skill** — lint target is the `skill/` subdir (or repo root for legacy repos).
- **Plugin** — lint target is the plugin root; manifest + each `skills/<name>/` checked.

> See `references/layouts.md` for layout diagrams, file-by-file conventions, and per-mode detection rules.

## Triage Workflow

**Target:** the skill directory to lint — current directory (`.`) or a path provided by the user.

### Step 1 — Get the full picture

```bash
./scripts/skill-lint.py check <target>
```

Review the output for errors and warnings; confirm the full picture before proceeding to Step 2.

### Step 2 — Fix Errors first

**Rule 1** (SKILL.md spec compliance) blocks publishing. Fix before anything else.

### Step 3 — Auto-fix Warnings

```bash
./scripts/skill-lint.py check <target> --fix
```

For fixable rules without CLI, use the templates in `references/fix-templates.md`.

Confirm no auto-fixable warnings remain before continuing to Step 4.

### Step 4 — Resolve remaining Warnings manually

CSO description prefix (Rule 11), Python invocations (Rule 13), README-tier sections in SKILL.md (Rule 19) — see the rule table below.

Confirm all remaining warnings are resolved (or explicitly accepted) before proceeding to Step 5.

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

Confirm the description and name function as pure routing signals before moving to Step 6.

### Step 6 — Semantic review: starter prompts

Rule 7 detects whether prompts exist, not whether they're useful. Read the Usage section starter prompts and ask: **do they reflect genuine, distinct trigger scenarios?**

Flag them if they:
- Are vague or generic (e.g. `Use this skill`, `Run the linter`)
- All describe the same scenario with minor wording variation
- Don't reflect the range of contexts a real user would encounter

Confirm starter prompts cover genuinely distinct use cases before proceeding to Step 7.

### Step 7 — Semantic review: content overlap

The linter does not check this. Ask: **is the same information conveyed in different words across SKILL.md and README?**

> See `references/semantic-rules.md` — Rule 8 for examples.

Flag paraphrased repetition. SKILL.md should be agent-focused (triage workflow, rules); README should be human-focused (installation, usage examples).

Confirm no paraphrased repetition remains before moving to Step 8.

### Step 8 — Semantic review: progressive disclosure

Rule 15 flags known reference-tier keywords, but not all reactive content has a recognizable heading. Ask: **would an agent look up this section reactively rather than read it upfront?**

> See `references/semantic-rules.md` — Rule 16 for examples.

Flag sections for `references/` if they:
- Are reference material regardless of their heading name (e.g. "Background", "How It Works")
- Are dense or conditional — even if short and not caught by Rule 15
- Are step-specific detail blocks that bulk up the main workflow without being needed upfront

Also ask: **when a section is conditional ("After…", "Once…", "If…"), does its heading or first line name a concrete trigger event the agent can observe?**

> See `references/semantic-rules.md` — Rule 27 for examples.

Flag conditional sections whose trigger is vague — "After reviewing the output", "Once you understand the context" — and would leave the agent guessing when to enter the section.

Confirm all reactive content has been moved to `references/` and all conditional sections name an observable trigger before proceeding to Step 9.

### Step 9 — Semantic review: multi-step workflow quality

Only apply this step when the skill has a multi-step workflow (3+ `### Step N` headings).

Read each step body and ask: **does every substantive step state how the agent knows it is done?**

> See `references/semantic-rules.md` — Rule 22 for examples.

Flag a step if its body describes only *what to do* with no exit condition, no gate phrase, no "proceed only when" signal. Trivially short steps (a single line) need no explicit gate.

Also ask: **does the workflow include at least one step that checks actual tool output, not just verbal claims?**

> See `references/semantic-rules.md` — Rule 23 for examples.

Flag the workflow if every step prescribes actions but none tells the agent to read what the tool actually returned.

Also ask: **if the workflow loops on tool output, does it name a retry cap and a fallback?**

> See `references/semantic-rules.md` — Rule 26 for examples.

Flag the workflow if it instructs the agent to retry, iterate, or wait for a tool to succeed but has no exit condition beyond "until it works".

Confirm all three questions are satisfied before proceeding to Step 10.

### Step 10 — Address Info items as polish

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
| 20 | Triage workflow has 3+ steps but no semantic review step (e.g. "Ask: does it…") | Info | Step 5–9 |
| 21 | Python entry-point scripts in `scripts/` lack PEP 723 inline dependency metadata | Warning | — |
| 24 | Plugin manifest `.claude-plugin/plugin.json` exists, parses, has `name` + `version` | Error | — |
| 25 | Skill scripts importing non-stdlib code declare a dep source (PEP 723, plugin-root pyproject.toml, or sibling dir) | Error | — |

Rules 24 and 25 only fire in plugin mode (when `.claude-plugin/plugin.json` is present at the lint target).

## CLI Reference

```bash
./scripts/skill-lint.py check .                            # Auto-detect: skill or plugin
./scripts/skill-lint.py check ./my-skill --fix             # Single-skill, auto-fix
./scripts/skill-lint.py check ./my-plugin                  # Plugin: validates manifest +
                                                           # iterates skills/<name>/
./scripts/skill-lint.py check ./my-skill --format json     # JSON output for CI
```

Exit code 1 on errors, 0 otherwise.
