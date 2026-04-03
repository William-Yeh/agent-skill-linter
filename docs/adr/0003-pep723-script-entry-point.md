# ADR-0003: PEP 723 inline script metadata as the entry point

Date: 2026-04-03

## Status

Accepted

## Context

The linter needs to be invocable by an installed agent without requiring the
user to know the package distribution URL or install a separate tool. Three
approaches were considered:

**Approach A — Published PyPI package**: `uvx --from agent-skill-linter
skill-lint check <target>`. Clean, but requires publishing to PyPI on every
release and pins the agent to a specific registry.

**Approach B — Git URL with uvx**: `uvx --from git+https://github.com/...
skill-lint check <target>`. No PyPI, but hard-codes a URL in SKILL.md and
every agent invocation. Fragile on forks or repo renames.

**Approach C — PEP 723 inline script**: Move Python source into `skill/scripts/`,
declare dependencies in a `# /// script` block inside `skill-lint.py`. Invoke
with `uv run ./scripts/skill-lint.py check <target>`. No URL, no registry,
no `pyproject.toml` inside `skill/`.

## Decision

Approach C. The entry point is `skill/scripts/skill-lint.py` with PEP 723
inline metadata:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "skills-ref",
#   "click",
#   "pyyaml",
#   "rich",
# ]
# ///
```

Sibling modules (`linter.py`, `rules.py`, `fixers.py`, `models.py`) live
alongside the entry point in `skill/scripts/`. The entry point inserts its
own directory into `sys.path` at startup so siblings resolve without a package
structure.

The `#!/usr/bin/env -S uv run` shebang allows direct execution (`chmod +x`)
without an explicit `uv run` prefix.

## Consequences

- `skill/` is self-contained: no `pyproject.toml`, no `uv.lock`, no package
  installation step. Agents run the script with a single `uv run` call.
- `uv` caches the resolved environment per script (keyed by dependency hash).
  First run installs; subsequent runs are instant from cache.
- The source is not importable as a Python package — `from rules import ...`
  only works after `sys.path` is set up via `conftest.py` (tests) or the
  entry-point's path insertion (runtime).
- `skill/scripts/` contains both executable scripts and supporting modules.
  Conventionally `scripts/` holds only executables; the trade-off was accepted
  to keep `skill/` flat and avoid a separate `src/` or `lib/` subdirectory
  within the installed skill.
- The root `pyproject.toml` lists runtime deps in `[dependency-groups] dev`
  for local `uv run pytest` convenience. This is a semantic mismatch documented
  with a comment; the PEP 723 header in `skill-lint.py` is the authoritative
  dependency declaration.

## Amendment (2026-04-03)

Rule 21 was added to enforce this pattern on *other* skills: any `.py` file in
`scripts/` that carries a shebang line (`#!/`) is identified as an entry point
and must declare its dependencies via a `# /// script` block. Module files
(no shebang) are excluded from the check.

The shebang is the chosen signal because it is both necessary (marks a file as
directly executable) and sufficient (module files never carry one). This avoids
the need to maintain a list of known entry-point filenames.
