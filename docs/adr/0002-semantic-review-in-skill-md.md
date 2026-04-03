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
Python.

Rationale:
- Agents already read SKILL.md as part of the triage workflow — the semantic
  steps are encountered naturally, at the right point in the workflow.
- No external API dependency or latency in the Python linter.
- Judgment quality scales with the invoking LLM, not a fixed model pinned in
  the codebase.
- Approach A would require API keys, error handling, and cost management — all
  complexity unrelated to the linter's core mission.

## Evolution

Initially, Python rules 11, 15, 16, and 18 provided mechanical pattern-matching
as a first pass, with Steps 5–8 extending coverage to cases those rules missed.

After further evaluation, rules 8 (content dedup), 12 (gerund name), 16 (heavy
step sections), and 18 (description conciseness) were **removed from Python
entirely**:

- Rule 8's 50% exact-line threshold missed paraphrased overlap and fired on
  legitimate shared code samples.
- Rule 12's gerund heuristic flagged valid short names (`pdf`, `commit`,
  `debug`) with no gerund segment.
- Rule 16's 30-line threshold was an arbitrary proxy for cognitive load.
- Rule 18's sentence-splitting on `.?!` falsely triggered on version strings
  and technical notation (`X.Y.Z`, `4xx/5xx`).

Their removal was deliberate: a mechanical proxy with a high false-positive rate
is worse than no check, because it trains users to ignore warnings. The agent
triage steps are the sole enforcement mechanism for these signals.

Concrete should-flag / should-not-flag examples for all four removed rules are
preserved in `skill/references/semantic-rules.md`, replacing the deleted unit
tests as the authoritative specification.

## Consequences

- Semantic checks only run when an agent invokes the skill; `skill-lint.py`
  CLI does not perform them.
- The rule table in SKILL.md has gaps at 8, 12, 16, and 18 — intentional,
  not omissions.
- If future LLMs support structured tool outputs, Approach A could be layered
  on top without changing the existing workflow.

## Amendment (2026-04-03)

Rule 20 was added as the constructive counterpart to the removal of Rules 8/12/16/18:
instead of detecting bad semantic patterns, it detects the *absence of semantic
coverage* — a triage workflow with 3+ steps but no `Ask:` prompt leaves quality
signals unchecked entirely.

The design principle is symmetric with the removals: Rule 20 fires only when the
structural threshold (≥ 3 steps) is met, preventing false positives on stub
SKILL.md files. The `Ask:` marker is the canonical signal; `read … and ask` is
the only accepted variant, keeping the pattern tight.
