# ADR-0005: Delegate AI-flavor detection to a sibling skill

Date: 2026-09-06

## Status

Accepted

## Context

Rule 28 adds a plain-prose check for human-facing documents (README and user
guides). Part of that check is detecting AI-flavored filler: stock phrases
such as "delve", "seamless", "it's worth noting", and their Chinese
equivalents.

The `critiquing-articles` skill in the same umbrella repo already owns this
problem. It ships a stdlib script (`pattern_density.py --patterns ai-tells`)
with about 25 bilingual regex families and a four-layer judgment guide
(lexical, construction, structure, tone) with a counteraction playbook. Its
word list rotates as vendors patch tells; its structural tests are durable.

Three ways to use it were considered:

**A — Shell out at lint time.** Rule 28 locates the sibling's script and runs
it. Install paths differ per agent (`~/.claude/skills/`, `.cursor/skills/`,
…) and the skill may be absent, so the mechanical rule would have an
environment-dependent result.

**B — Vendor the pattern list.** Copy the ai-tells regexes into `rules.py`.
Duplicates code across two repos by the same author and drifts the moment the
upstream list changes.

**C — Delegate at the skill level.** A semantic step in SKILL.md tells the
agent: if `critiquing-articles` is among its available skills, run its
AI-flavor audit on each human-facing document with a README genre note;
otherwise apply an inline four-layer checklist. Rule 28 keeps only signals the
sibling does not cover.

## Decision

Approach C.

- Rule 28 (mechanical, Info) checks README-specific signals only: marketing
  superlatives, throat-clearing openers, lead-paragraph placement, and
  language-agnostic sentence and paragraph length. Its message names the
  sibling skill and its install command.
- A new semantic step performs the delegated audit. The genre note tells the
  agent that bullet lists, bold-colon items, install steps, and code are normal
  in a README, and that em-dash density is discounted below three per
  paragraph.
- `localizing-taiwan-chinese` is not invoked by default. It bundles Taiwan
  localization, which is a locale choice rather than a plainness concern, and
  one of its phases needs a remote endpoint. The step suggests it only when the
  document is Traditional Chinese and mainland-lexicon hits appear.

## Consequences

- Rule 28 will not flag "delve" or similar words. A reader who expects it to
  should look at the semantic step, not the Python.
- The linter gains upstream improvements to the tell list without a release.
- The two skills are now coupled by name. Renaming `critiquing-articles` or its
  AI-flavor mode requires a matching edit in this skill's SKILL.md and
  `references/semantic-rules.md`.
- Agents without the sibling installed get a weaker but still usable check via
  the inline checklist.
