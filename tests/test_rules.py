"""Tests for all lint rules."""

from __future__ import annotations

import shutil
from pathlib import Path

from agent_skill_linter.linter import lint_skill
from agent_skill_linter.models import Severity
from agent_skill_linter import rules

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def results_for_rule(results, rule_id):
    return [r for r in results if r.rule_id == rule_id]


# ---------------------------------------------------------------------------
# Valid skill — should pass clean
# ---------------------------------------------------------------------------


class TestValidSkill:
    def test_no_errors(self):
        results = lint_skill(FIXTURES / "valid-skill")
        errors = [r for r in results if r.severity == Severity.ERROR]
        assert errors == [], f"Unexpected errors: {errors}"

    def test_no_warnings(self):
        results = lint_skill(FIXTURES / "valid-skill")
        warnings = [r for r in results if r.severity == Severity.WARNING]
        assert warnings == [], f"Unexpected warnings: {warnings}"


# ---------------------------------------------------------------------------
# Rule 1: SKILL.md spec compliance
# ---------------------------------------------------------------------------


class TestRule1:
    def test_missing_skill_md(self, tmp_path):
        results = rules.check_spec_compliance(tmp_path)
        assert len(results) == 1
        assert results[0].severity == Severity.ERROR
        assert "SKILL.md" in results[0].message

    def test_valid_skill_md(self):
        results = rules.check_spec_compliance(FIXTURES / "valid-skill")
        assert results == []


# ---------------------------------------------------------------------------
# Rule 2: LICENSE
# ---------------------------------------------------------------------------


class TestRule2:
    def test_missing_license(self):
        results = rules.check_license(FIXTURES / "missing-license")
        assert len(results) == 1
        assert results[0].fixable

    def test_valid_license(self):
        results = rules.check_license(FIXTURES / "valid-skill")
        assert results == []


# ---------------------------------------------------------------------------
# Rule 3: metadata.author
# ---------------------------------------------------------------------------


class TestRule3:
    def test_missing_author(self):
        results = rules.check_author(FIXTURES / "missing-author")
        assert len(results) == 1
        assert results[0].fixable

    def test_valid_author(self):
        results = rules.check_author(FIXTURES / "valid-skill")
        assert results == []


# ---------------------------------------------------------------------------
# Rule 4: README badges
# ---------------------------------------------------------------------------


class TestRule4:
    def test_no_badges(self):
        results = rules.check_readme_badges(FIXTURES / "no-badges")
        assert len(results) == 3  # CI, License, Agent Skills
        assert all(r.fixable for r in results)

    def test_valid_badges(self):
        results = rules.check_readme_badges(FIXTURES / "valid-skill")
        assert results == []


# ---------------------------------------------------------------------------
# Rule 5: CI workflow
# ---------------------------------------------------------------------------


class TestRule5:
    def test_no_ci(self):
        results = rules.check_ci_workflow(FIXTURES / "no-ci")
        assert len(results) == 1
        assert results[0].fixable

    def test_valid_ci(self):
        results = rules.check_ci_workflow(FIXTURES / "valid-skill")
        assert results == []


# ---------------------------------------------------------------------------
# Rule 6: Installation section
# ---------------------------------------------------------------------------


class TestRule6:
    def test_no_install_section(self):
        results = rules.check_installation_section(FIXTURES / "no-install-section")
        assert len(results) == 1
        assert results[0].fixable

    def test_valid_install_section(self):
        results = rules.check_installation_section(FIXTURES / "valid-skill")
        assert results == []


# ---------------------------------------------------------------------------
# Rule 7: Usage section
# ---------------------------------------------------------------------------


class TestRule7:
    def test_no_usage_section(self):
        results = rules.check_usage_section(FIXTURES / "no-usage-section")
        assert len(results) == 1
        assert results[0].fixable

    def test_valid_usage_section(self):
        results = rules.check_usage_section(FIXTURES / "valid-skill")
        assert results == []


# ---------------------------------------------------------------------------
# Rule 8: Content dedup
# ---------------------------------------------------------------------------


class TestRule8:
    def test_heavy_overlap(self, tmp_path):
        body = "\n".join(f"This is a detailed line number {i} of content" for i in range(50))
        (tmp_path / "SKILL.md").write_text(f"---\nname: x\ndescription: x\n---\n\n{body}\n")
        (tmp_path / "README.md").write_text(f"# Readme\n\n{body}\n")
        results = rules.check_content_dedup(tmp_path)
        assert len(results) == 1
        assert results[0].severity == Severity.INFO

    def test_no_overlap(self):
        results = rules.check_content_dedup(FIXTURES / "valid-skill")
        assert results == []


# ---------------------------------------------------------------------------
# Rule 9: SKILL.md body length
# ---------------------------------------------------------------------------


class TestRule9:
    def test_long_body(self):
        results = rules.check_skill_body_length(FIXTURES / "long-body")
        assert len(results) == 1
        assert results[0].severity == Severity.INFO

    def test_normal_body(self):
        results = rules.check_skill_body_length(FIXTURES / "valid-skill")
        assert results == []


# ---------------------------------------------------------------------------
# Rule 10: Non-standard dirs
# ---------------------------------------------------------------------------


class TestRule10:
    def test_nonstandard_dirs(self, tmp_path):
        (tmp_path / "SKILL.md").write_text("---\nname: x\ndescription: x\n---\n")
        (tmp_path / "weird_stuff").mkdir()
        results = rules.check_nonstandard_dirs(tmp_path)
        assert len(results) == 1
        assert "weird_stuff" in results[0].message

    def test_standard_dirs(self, tmp_path):
        (tmp_path / "SKILL.md").write_text("---\nname: x\ndescription: x\n---\n")
        (tmp_path / "scripts").mkdir()
        (tmp_path / "references").mkdir()
        results = rules.check_nonstandard_dirs(tmp_path)
        assert results == []


# ---------------------------------------------------------------------------
# Integration: --fix on broken fixture
# ---------------------------------------------------------------------------


class TestFixIntegration:
    def test_fix_missing_license(self, tmp_path):
        """Copy no-license fixture, apply fix, re-lint — rule 2 should clear."""
        shutil.copytree(FIXTURES / "missing-license", tmp_path / "skill", dirs_exist_ok=True)
        skill_dir = tmp_path / "skill"

        # Verify it fails first
        results = lint_skill(skill_dir)
        r2 = results_for_rule(results, 2)
        assert len(r2) > 0

        # Apply fix non-interactively by writing LICENSE directly
        (skill_dir / "LICENSE").write_text(
            "Apache License\nVersion 2.0\nCopyright 2026 Test\n"
        )

        # Re-lint
        results = lint_skill(skill_dir)
        r2 = results_for_rule(results, 2)
        assert len(r2) == 0

    def test_fix_ci_workflow(self, tmp_path):
        """Apply CI fixer programmatically."""
        shutil.copytree(FIXTURES / "no-ci", tmp_path / "skill", dirs_exist_ok=True)
        skill_dir = tmp_path / "skill"

        from agent_skill_linter.fixers import fix_ci_workflow
        from agent_skill_linter.models import LintResult

        fix_ci_workflow(skill_dir, LintResult(rule_id=5, severity=Severity.WARNING, message=""))

        results = lint_skill(skill_dir)
        r5 = results_for_rule(results, 5)
        assert len(r5) == 0
