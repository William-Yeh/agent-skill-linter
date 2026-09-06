# ADR-0007: Claude Code frontmatter extensions warn, they do not error

Date: 2026-09-06

## Status

Accepted

## Context

Rule 1 delegates SKILL.md frontmatter validation to `skills-ref`, the Agent
Skills reference validator. It allows exactly six fields (`name`,
`description`, `license`, `compatibility`, `metadata`, `allowed-tools`) and
errors on anything else.

Claude Code documents fourteen further fields for SKILL.md, among them
`disable-model-invocation`, `user-invocable`, `argument-hint`, `model`,
`context`, `agent`, `hooks`, and `paths`. Some are load-bearing:
`disable-model-invocation: true` is how a skill promises to run only when the
user invokes it. Claude Code reads these fields only at the top level, so
tucking them under `metadata:` to satisfy the validator loses the behaviour.

The concrete case was the `kaizen` skill, whose own ADR records
`disable-model-invocation: true` as a design property. Rule 1 reported it as
an error, which blocks publishing, and the only spec-clean fix would have
changed the skill's behaviour.

## Decision

`rules.CLAUDE_CODE_FRONTMATTER_EXTENSIONS` lists the documented fields, with
the docs URL. Rule 1 parses the frontmatter once, removes those keys,
validates the remainder with `skills-ref` exactly as before, and emits one
Rule 1 **warning** naming the extension fields present. Unknown fields outside
the list remain errors. The warning text says why it is a warning: other
runtimes ignore the fields, and claude.ai / Skills API uploads reject them.

Rejected:

- Silently accepting the fields. The author should learn the skill is Claude
  Code-only.
- Keeping them as errors. A validator would be overriding a documented runtime
  feature.
- A `--claude-code` flag. Configuration for a decision the linter can make
  from the field name.

Restructuring the rule also collapsed its two code paths (`.git` root via
`skills_ref.validate`, subdir via `validate_metadata`) into one parse and one
`validate_metadata` call. The root-only directory-name check from ADR-0001 is
preserved and now has a characterisation test.

## Consequences

- A Claude Code-only skill passes Rule 1 with a warning it can accept in
  triage Step 4. A skill meant to publish cross-platform sees exactly which
  fields to drop.
- The field list will drift as Claude Code adds fields. It is one `frozenset`
  with a source link, and a property test asserts that any subset of it yields
  one warning naming each field, so extending the list needs no new tests.
- Rule 1 now has two severities. The rule table says so.
