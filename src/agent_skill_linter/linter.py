"""Orchestrates all lint rules and returns results."""

from __future__ import annotations

from pathlib import Path

from agent_skill_linter.models import LintResult


def lint_skill(path: str | Path) -> list[LintResult]:
    """Run all lint rules on a skill directory and return results."""
    from agent_skill_linter import rules

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
        rules.check_content_dedup,
        rules.check_skill_body_length,
        rules.check_nonstandard_dirs,
        rules.check_cso_description,
        rules.check_cso_name,
        rules.check_cso_description_conciseness,
        rules.check_python_invocations,
        rules.check_progressive_disclosure,
        rules.check_semantic_sections,
        rules.check_step_conditional_sections,
        rules.check_skill_isolation,
        rules.check_readme_tier_in_skill,
    ]
    for fn in rule_fns:
        results.extend(fn(skill_dir))

    return results
