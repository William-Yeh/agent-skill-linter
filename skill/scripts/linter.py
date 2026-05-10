"""Orchestrates lint rules and returns results.

Two entry points:
- `lint_skill(path)` — single-skill mode: applies all per-skill rules to one
  skill directory.
- `lint_plugin(path)` — plugin mode: validates the manifest, then iterates
  `skills/*/` running the per-skill rules on each, plus plugin-level rules.

`detect_layout(path)` picks between them based on `.claude-plugin/plugin.json`.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from models import LintResult


def lint_skill(path: str | Path) -> list[LintResult]:
    """Run all per-skill lint rules on a skill directory and return results."""
    import rules

    skill_dir = Path(path).resolve()
    results: list[LintResult] = []

    rule_fns = [
        rules.check_spec_compliance,
        rules.check_license,
        rules.check_author,
        rules.check_readme_badges,
        rules.check_ci_workflow,
        rules.check_installation_section,
        rules.check_usage_section,
        rules.check_skill_body_length,
        rules.check_nonstandard_dirs,
        rules.check_cso_description,
        rules.check_python_invocations,
        rules.check_progressive_disclosure,
        rules.check_semantic_sections,
        rules.check_skill_isolation,
        rules.check_readme_tier_in_skill,
        rules.check_triage_semantic_balance,
        rules.check_pep723_entry_points,
    ]
    for fn in rule_fns:
        results.extend(fn(skill_dir))

    return results


def lint_plugin(path: str | Path) -> list[LintResult]:
    """Run plugin-level rules and per-skill rules across every `skills/<name>/`.

    Per-skill results have their `file` field rewritten relative to the plugin
    root so the user can see which skill each finding came from.
    """
    import rules

    plugin_root = Path(path).resolve()
    results: list[LintResult] = []

    # Plugin-level rules.
    results.extend(rules.check_plugin_manifest(plugin_root))
    results.extend(rules.check_local_package_deps(plugin_root))

    # Each skill, prefixed with its skill name in `file` for clarity.
    skills_dir = plugin_root / "skills"
    if not skills_dir.is_dir():
        return results

    # Per-skill findings whose `file` resolves to a shared plugin-root artifact
    # (README.md, LICENSE, .github/workflows/...) would otherwise be reported once
    # per skill. Dedupe across skills so each plugin-scoped issue surfaces once.
    plugin_scoped_files = {"README.md", "LICENSE", "pyproject.toml"}
    seen_plugin_scoped: set[tuple[int, str | None, str]] = set()

    for skill_dir in sorted(skills_dir.iterdir()):
        if not (skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file()):
            continue
        skill_results = lint_skill(skill_dir)
        skill_relpath = skill_dir.relative_to(plugin_root)
        for r in skill_results:
            is_plugin_scoped = (
                r.file in plugin_scoped_files
                or (r.file and r.file.startswith(".github/"))
            )
            if is_plugin_scoped:
                key = (r.rule_id, r.file, r.message)
                if key in seen_plugin_scoped:
                    continue
                seen_plugin_scoped.add(key)
                results.append(r)  # plugin-root file path stays unprefixed
                continue
            new_file = (
                str(skill_relpath / r.file)
                if r.file and not r.file.startswith(str(skill_relpath))
                else r.file
            )
            results.append(replace(r, file=new_file))
    return results


def detect_layout(path: str | Path) -> str:
    """Return 'plugin' if `path` is a plugin root, else 'skill'."""
    target = Path(path).resolve()
    return "plugin" if (target / ".claude-plugin" / "plugin.json").is_file() else "skill"
