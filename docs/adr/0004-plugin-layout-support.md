# ADR-0004: Recognise Claude Code plugin layouts as a second lint mode

Date: 2026-05-10

## Status

Accepted

## Context

ADR-0001 established the single-skill subdirectory layout (`my-skill/skill/`).
The linter assumed every lint target was one skill — the CLI took a single
path, all rules ran against it, and `_repo_root()` climbed via `.git` /
`.gitroot` only.

Claude Code plugins introduce a second valid layout: a marketplace artifact
that bundles **multiple** skills, optional commands/hooks/agents, and optional
shared library code under one identity, with a manifest at
`.claude-plugin/plugin.json`. Cached plugins on disk look like:

```
my-plugin/
├── .claude-plugin/plugin.json   ← required marker
├── skills/<name>/SKILL.md       ← one or more skills
├── <package_name>/              ← optional shared Python code
├── commands/, agents/, hooks/   ← optional component types
├── pyproject.toml               ← optional; required if scripts import a
│                                  local package not declared via PEP 723
├── README.md, LICENSE
└── .github/workflows/
```

The motivating concrete case was `narrative-analysis`, an umbrella plugin
hosting `cld-analysis` and `crt-analysis` siblings that share a non-trivial
`narrative_analysis_core` package. Before this work, running the linter
against the plugin root failed (no SKILL.md at root) and against each skill
silently skipped Rule 13 because `_uses_uv()` only inspected the skill
directory, not the plugin-root `pyproject.toml`. Critically, no rule caught
the *deployment* failure mode: skill scripts importing a plugin-root sibling
package that won't exist at the lint target's view of the world.

## Decision

Treat plugin and skill repos as two distinct lint modes, auto-detected from
the lint target.

### Detection

Add `linter.detect_layout(path)`:

- Return `"plugin"` if `path / ".claude-plugin" / "plugin.json"` is a file.
- Return `"skill"` otherwise.

The CLI's `check` command dispatches to `lint_plugin()` or `lint_skill()`
accordingly. No new subcommand or flag.

### Path resolution

Extend `_repo_root()` to recognise `.claude-plugin/plugin.json` as a third
root marker (alongside `.git` and `.gitroot`). This makes per-skill rules
(Rules 2, 4, 5, 6, 7) climb to the plugin root for shared artifacts even when
the plugin isn't a git checkout (test fixtures, fresh extractions).

Update `_uses_uv()` and `_has_non_stdlib_deps()` to consult both the skill
directory and the resolved repo/plugin root, so Rule 13 fires on
plugin-rooted `uv.lock` / `pyproject.toml`.

### Plugin orchestration

Add `linter.lint_plugin(plugin_root)`:

1. Run plugin-scoped rules (24 manifest, 25 local-package deps).
2. Iterate `skills/<name>/` and run the per-skill rule pack on each.
3. Dedupe findings whose `file` resolves to a shared plugin-root artifact
   (`README.md`, `LICENSE`, `pyproject.toml`, `.github/...`) so each
   plugin-scoped issue surfaces once, not once per skill.
4. Prefix the remaining per-skill findings' `file` with the skill's relative
   path (`skills/cld-analysis/SKILL.md`) so multi-skill output is navigable.

### New rules

- **Rule 24** — `.claude-plugin/plugin.json` exists, parses, declares required
  keys (`name`, `version`). Severity: Error. Only fires when the manifest is
  present (silent on single-skill repos).
- **Rule 25** — Skill scripts in `skills/<name>/scripts/*.py` that import
  non-stdlib code must declare a dep source: PEP 723 inline metadata,
  plugin-root `pyproject.toml`, or a sibling directory at plugin root
  (sys.path-injection pattern). Severity: Error. Catches the original
  deployment failure mode.

  Rule 25 deliberately treats *presence* of a PEP 723 block as sufficient
  rather than validating that `dependencies = [...]` covers every import name.
  Distribution-vs-import name mapping (`pyyaml` → `yaml`,
  `beautifulsoup4` → `bs4`, `pillow` → `PIL`) is impossible to do reliably
  without installing packages. PEP 723's presence is the analyst's contract
  that runtime deps are declared inline; trust them on the contents.

## Consequences

- Single-skill linting is unchanged: `lint_skill()` is the existing
  implementation and the CLI still defaults to it when no manifest is
  present.
- Plugin linting gains automatic dispatch with no new flags. Running
  `skill-lint check ./my-plugin` does the right thing whether the path is a
  skill or a plugin.
- Rules 24 and 25 are silent on single-skill repos by design (each is gated
  by `_is_plugin_root()`), so adding them imposes no false positives on the
  legacy path.
- The fixture matrix grows by one: `tests/fixtures/valid-plugin/` exercises
  manifest validation, the sys.path-injection variant of Rule 25 (sibling
  directory match), the PEP-723-grants-pass variant of Rule 25, plugin-root
  dedupe of Rule 4/5/6/7 findings, and `_repo_root()` resolution via the
  manifest.
- ADR-0001's prescient note about "supporting arbitrarily nested skill
  directories (e.g. monorepos, plugin trees)" is materialised here. No
  retroactive change to ADR-0001.
- Maintenance burden: two layout modes to keep in sync. Mitigated by the
  per-skill rule pack being shared between modes — only the orchestration
  differs.
