# ADR-0006: Resolve a repo-root lint target to its `skill/` subdirectory

Date: 2026-09-06

## Status

Accepted

## Context

ADR-0001 moved SKILL.md into `skill/` and documented `skill/` as the lint
target. ADR-0004 added `detect_layout()`, which distinguishes plugin from skill
but has no notion of "repo root of a `skill/` layout". Running `check .` from
such a root therefore ran the per-skill rules against the root: Rule 1 reported
SKILL.md missing (exit 1), and Rule 17 told the user to move SKILL.md into
`skill/`, which was already done. Rule 17 never checked its own premise; it
fired on `.git` plus non-skill artifacts alone.

The linter's recommended layout was the one case it could not lint from the
root, and its advice in that case was false.

## Decision

- `linter.resolve_target(path)` returns `(layout, directory to lint)`. Plugin
  manifest present: `("plugin", path)`. No SKILL.md at the path but
  `skill/SKILL.md` present: `("skill", path / "skill")`. Otherwise:
  `("skill", path)`. A SKILL.md at the path always wins, so legacy root layouts
  are unchanged. `detect_layout()` remains as a wrapper returning the layout.
- The CLI lints the resolved directory and, when it differs from the argument,
  prints one line on stderr. stdout stays machine-readable for `--format json`.
- Rule 17 returns nothing unless SKILL.md is actually at the target, using the
  same finder Rule 1 uses.

## Consequences

- `check .` from any single-skill repo, legacy or `skill/`, does the right
  thing. Documentation still names `skill/` as the canonical target.
- Rule 17 can no longer state a false premise. Its message text is unchanged.
- Tests: `TestResolveTarget` pins the precedence rules. `tests/test_cli.py`
  drives the `check` command through click's `CliRunner` on a copy of the
  subdir fixture with a real `.git` marker, which is the exact scenario that
  failed. `TestRule17` gains the false-premise case.
