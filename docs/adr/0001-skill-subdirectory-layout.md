# ADR-0001: Isolate skill files in a `skill/` subdirectory

Date: 2026-04-02

## Status

Accepted

## Context

`npx skills add <owner>/<repo>` (vercel-labs/skills) installs skill files by
locating SKILL.md in the repository and copying its containing directory. There
is no `.skillsignore` or equivalent configuration mechanism — exclusions are
hardcoded to dotfiles, `.git`, `__pycache__`, and `metadata.json`.

When SKILL.md lived at the repo root, `npx skills add` would copy the entire
repository — including `src/`, `tests/`, `pyproject.toml`, `uv.lock`, and
other artifacts that agents have no use for. This bloated the installed skill
and triggered Rule 17 (skill isolation) on the linter's own skill.

## Decision

Move `SKILL.md` and `references/` into a `skill/` subdirectory. The linter
source (`src/`), tests, and build manifests remain at the repo root.

`npx skills add William-Yeh/agent-skill-linter` now installs only `skill/`,
which contains exactly what an agent needs to invoke the skill.

The linter itself was updated to support this layout:
- A `_repo_root()` helper climbs one level when the skill directory is a direct
  subdirectory of a `.git`-bearing parent.
- A `_repo_path(skill_dir, name)` helper resolves repo-level artifacts
  (LICENSE, README, `.github/`) by checking `skill_dir` first, then the repo
  root — allowing rules 2, 4, 5, 6, 7, and 8 to work correctly when linting
  subdir skills.
- `check_spec_compliance` skips the `skills_ref` directory-name check for
  subdir skills (the installed directory name comes from SKILL.md `name`, not
  the source path).

## Consequences

- Agents installing via `npx skills add` receive a lean install (~2 files).
- The linter can lint both repo-root skills (legacy) and subdir skills (this
  layout) without configuration.
- Manual installation instructions in README must specify the target directory
  name explicitly (e.g. `~/.claude/skills/agent-skill-linter/`) rather than
  the generic skills folder.
- `_repo_root` intentionally climbs only one level to prevent test fixture
  contamination: deeply nested test fixtures should not accidentally resolve to
  the project's own LICENSE/README.
