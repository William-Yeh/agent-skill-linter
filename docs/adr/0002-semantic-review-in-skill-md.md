# ADR-0002: Encode semantic lint steps in SKILL.md, not Python

Date: 2026-04-02

## Status

Accepted

## Context

Several quality signals cannot be reliably checked by regex or static analysis:

- Is the `description` frontmatter a pure routing signal, or does it read as a
  feature summary?
- Do the README starter prompts reflect genuinely distinct trigger scenarios,
  or are they paraphrases of each other?
- Is content between SKILL.md and README merely paraphrased repetition (not
  detectable by line-diff)?
- Would an agent look up a section reactively, even if its heading doesn't
  match the reference-tier keyword list?

Two approaches were considered:

**Approach A — LLM call in Python**: A `rules.check_semantic_*` function calls
an LLM API and returns `LintResult`s. This keeps all lint logic in one place
and produces structured JSON output.

**Approach B — Triage steps in SKILL.md**: The SKILL.md triage workflow
includes explicit steps (5–8) that instruct the invoking agent to apply the
semantic judgments. The Python linter handles only what pattern-matching can
reliably detect.

## Decision

Approach B. Semantic review lives in `skill/SKILL.md` Steps 5–8, not in
`rules.py`.

Rationale:
- Agents already read SKILL.md as part of the triage workflow — the semantic
  steps are encountered naturally, at the right point in the workflow.
- No external API dependency or latency in the Python linter.
- Judgment quality scales with the invoking LLM, not a fixed model pinned in
  the codebase.
- The Python rules (11, 15, 16, 18) still catch the mechanical patterns;
  Steps 5–8 extend coverage to cases those rules miss.
- Approach A would require API keys, error handling, and cost management — all
  complexity unrelated to the linter's core mission.

## Consequences

- Semantic checks only run when an agent invokes the skill; `skill-lint check`
  CLI does not perform them.
- The `Auto-fix` column in the rule table uses `Step N` as a pointer for rules
  with semantic counterparts, documenting the split clearly.
- If future LLMs support structured tool outputs, Approach A could be layered
  on top without changing the existing workflow.
