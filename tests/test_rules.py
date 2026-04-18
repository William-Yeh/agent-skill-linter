"""Tests for all lint rules."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from linter import lint_skill
from models import Severity
import rules

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
    @pytest.fixture(scope="class")
    def lint_results(self):
        return lint_skill(FIXTURES / "valid-skill")

    def test_no_errors(self, lint_results):
        errors = [r for r in lint_results if r.severity == Severity.ERROR]
        assert errors == [], f"Unexpected errors: {errors}"

    def test_no_warnings(self, lint_results):
        warnings = [r for r in lint_results if r.severity == Severity.WARNING]
        assert warnings == [], f"Unexpected warnings: {warnings}"


# ---------------------------------------------------------------------------
# Valid skill — subdir layout (skill/ subdir, repo artifacts at root)
# ---------------------------------------------------------------------------


class TestValidSkillSubdir:
    """Canonical layout: SKILL.md in skill/, repo artifacts (README, LICENSE, .github/) at root.

    NOTE: the fixture uses a plain file named .gitroot (not .git) as the repo-root marker.
    Git cannot track files named .git inside subdirectories; _repo_root() accepts both.
    Do not rename it to .git — git will silently ignore it and the fixture will break on clone.
    """

    SKILL_DIR = FIXTURES / "valid-skill-subdir" / "skill"

    @pytest.fixture(scope="class")
    def lint_results(self):
        return lint_skill(self.SKILL_DIR)

    def test_no_errors(self, lint_results):
        errors = [r for r in lint_results if r.severity == Severity.ERROR]
        assert errors == [], f"Unexpected errors: {errors}"

    def test_no_warnings(self, lint_results):
        warnings = [r for r in lint_results if r.severity == Severity.WARNING]
        assert warnings == [], f"Unexpected warnings: {warnings}"

    def test_repo_root_resolves_to_fixture_parent(self):
        """_repo_root must resolve to valid-skill-subdir/, not the linter's own repo root."""
        repo_root = rules._repo_root(self.SKILL_DIR)
        assert repo_root == FIXTURES / "valid-skill-subdir"

    def test_rule17_does_not_fire(self, lint_results):
        """Rule 17 must not fire: SKILL.md is in skill/, not the repo root."""
        assert results_for_rule(lint_results, 17) == []


# ---------------------------------------------------------------------------
# _repo_root helper
# ---------------------------------------------------------------------------


class TestRepoRoot:
    def test_direct_subdir(self, tmp_path):
        """skill/ one level under .git → parent is repo root."""
        (tmp_path / ".git").mkdir()
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        assert rules._repo_root(skill_dir) == tmp_path

    def test_deeply_nested(self, tmp_path):
        """skill/ three levels under .git → repo root found by walking up."""
        (tmp_path / ".git").mkdir()
        skill_dir = tmp_path / "plugins" / "myplugin" / "skill"
        skill_dir.mkdir(parents=True)
        assert rules._repo_root(skill_dir) == tmp_path

    def test_no_git_returns_self(self, tmp_path):
        """No .git anywhere → falls back to skill_dir itself."""
        skill_dir = tmp_path / "skill"
        skill_dir.mkdir()
        assert rules._repo_root(skill_dir) == skill_dir

    def test_at_repo_root(self, tmp_path):
        """skill_dir IS the repo root (SKILL.md at root) → returns itself."""
        (tmp_path / ".git").mkdir()
        assert rules._repo_root(tmp_path) == tmp_path


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
    def test_missing_license(self, tmp_path):
        shutil.copytree(FIXTURES / "missing-license", tmp_path / "skill")
        results = rules.check_license(tmp_path / "skill")
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
    def test_no_ci(self, tmp_path):
        shutil.copytree(FIXTURES / "no-ci", tmp_path / "skill")
        results = rules.check_ci_workflow(tmp_path / "skill")
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

    def test_usage_section_missing_prompts(self, tmp_path):
        (tmp_path / "README.md").write_text(
            "# Skill\n\n## Usage\n\nSome text.\n\n### CLI usage\n\n```bash\nfoo\n```\n"
        )
        results = rules.check_usage_section(tmp_path)
        messages = [r.message for r in results]
        assert any("starter prompt" in m for m in messages)

    def test_usage_section_missing_cli(self, tmp_path):
        (tmp_path / "README.md").write_text(
            "# Skill\n\n## Usage\n\nAfter installing:\n\n- `Try this prompt`\n"
        )
        results = rules.check_usage_section(tmp_path)
        messages = [r.message for r in results]
        assert any("CLI" in m for m in messages)


# ---------------------------------------------------------------------------
# Rule 8: Content dedup
# ---------------------------------------------------------------------------


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
# Rule 11: CSO description
# ---------------------------------------------------------------------------


class TestRule11:
    def test_description_not_use_when(self, tmp_path):
        (tmp_path / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: Lint skills for compliance.\n---\n\n# Body\n"
        )
        results = rules.check_cso_description(tmp_path)
        assert len(results) == 1
        assert results[0].severity == Severity.WARNING
        assert "Use when" in results[0].message

    def test_description_starts_use_when(self, tmp_path):
        (tmp_path / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: Use when linting a skill before publishing.\n---\n\n# Body\n"
        )
        results = rules.check_cso_description(tmp_path)
        assert results == []

    def test_valid_skill(self):
        results = rules.check_cso_description(FIXTURES / "valid-skill")
        assert results == []


# ---------------------------------------------------------------------------
# Rule 13: Python invocation consistency
# ---------------------------------------------------------------------------

_UV_PYPROJECT = (
    '[project]\nname = "foo"\ndependencies = ["click"]\n'
    '[build-system]\nrequires = ["uv_build>=0.1"]\nbuild-backend = "uv_build"\n'
)


class TestRule13:
    def _setup_uv_project(self, tmp_path, readme=None, ci_yml=None):
        (tmp_path / "uv.lock").write_text("")
        (tmp_path / "pyproject.toml").write_text(_UV_PYPROJECT)
        if readme is not None:
            (tmp_path / "README.md").write_text(readme)
        if ci_yml is not None:
            wf = tmp_path / ".github" / "workflows"
            wf.mkdir(parents=True)
            (wf / "ci.yml").write_text(ci_yml)

    def test_bare_python_in_readme(self, tmp_path):
        self._setup_uv_project(tmp_path, readme="# Docs\n\n```bash\npython scripts/run.py\n```\n")
        results = rules.check_python_invocations(tmp_path)
        assert len(results) == 1
        assert results[0].rule_id == 13
        assert results[0].severity == Severity.WARNING
        assert "README.md" in results[0].message

    def test_bare_python3_in_readme(self, tmp_path):
        self._setup_uv_project(tmp_path, readme="# Docs\n\n```bash\npython3 scripts/run.py\n```\n")
        results = rules.check_python_invocations(tmp_path)
        assert len(results) == 1

    def test_uv_run_python_is_ok(self, tmp_path):
        self._setup_uv_project(tmp_path, readme="# Docs\n\n```bash\nuv run python scripts/run.py\n```\n")
        assert rules.check_python_invocations(tmp_path) == []

    def test_heredoc_exception(self, tmp_path):
        readme = "# Docs\n\n```bash\npython3 - <<'EOF'\nimport sys\nprint(sys.version)\nEOF\n```\n"
        self._setup_uv_project(tmp_path, readme=readme)
        assert rules.check_python_invocations(tmp_path) == []

    def test_no_uv_project(self, tmp_path):
        # Plain setuptools project with no uv.lock and no uv_build backend
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "foo"\ndependencies = ["click"]\n'
            '[build-system]\nrequires = ["setuptools"]\nbuild-backend = "setuptools.build_meta"\n'
        )
        (tmp_path / "README.md").write_text("# Docs\n\n```bash\npython3 run.py\n```\n")
        assert rules.check_python_invocations(tmp_path) == []

    def test_empty_deps(self, tmp_path):
        (tmp_path / "uv.lock").write_text("")
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "foo"\ndependencies = []\n')
        (tmp_path / "README.md").write_text("# Docs\n\n```bash\npython3 run.py\n```\n")
        assert rules.check_python_invocations(tmp_path) == []

    def test_bare_python_in_ci_yml(self, tmp_path):
        self._setup_uv_project(tmp_path, ci_yml="steps:\n  - run: python3 scripts/foo.py\n")
        results = rules.check_python_invocations(tmp_path)
        assert len(results) == 1
        assert ".github/workflows/ci.yml" in results[0].file

    def test_uv_run_in_ci_yml_is_ok(self, tmp_path):
        self._setup_uv_project(tmp_path, ci_yml="steps:\n  - run: uv run python scripts/foo.py\n")
        assert rules.check_python_invocations(tmp_path) == []

    def test_yaml_extension_scanned(self, tmp_path):
        (tmp_path / "uv.lock").write_text("")
        (tmp_path / "pyproject.toml").write_text(_UV_PYPROJECT)
        wf = tmp_path / ".github" / "workflows"
        wf.mkdir(parents=True)
        (wf / "ci.yaml").write_text("steps:\n  - run: python3 scripts/foo.py\n")
        results = rules.check_python_invocations(tmp_path)
        assert len(results) == 1
        assert ".github/workflows/ci.yaml" in results[0].file

    def test_non_ci_yaml_ignored(self, tmp_path):
        self._setup_uv_project(tmp_path)
        (tmp_path / "docker-compose.yml").write_text("services:\n  app:\n    run: python3 app.py\n")
        assert rules.check_python_invocations(tmp_path) == []

    def test_valid_skill_passes(self):
        assert rules.check_python_invocations(FIXTURES / "valid-skill") == []


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

        from fixers import fix_ci_workflow
        from models import LintResult

        fix_ci_workflow(skill_dir, LintResult(rule_id=5, severity=Severity.WARNING, message=""))

        results = lint_skill(skill_dir)
        r5 = results_for_rule(results, 5)
        assert len(r5) == 0


# ---------------------------------------------------------------------------
# Rule 14: Progressive disclosure
# ---------------------------------------------------------------------------


class TestRule14:
    def test_detects_embedded_templates(self):
        results = rules.check_progressive_disclosure(FIXTURES / "dense-skill")
        assert len(results) == 1
        assert results[0].rule_id == 14
        assert results[0].fixable is True
        assert "Templates" in results[0].message

    def test_clean_skill_passes(self):
        results = rules.check_progressive_disclosure(FIXTURES / "valid-skill")
        assert results == []

    def test_fix_moves_section_to_references(self, tmp_path):
        shutil.copytree(FIXTURES / "dense-skill", tmp_path / "skill", dirs_exist_ok=True)
        skill_dir = tmp_path / "skill"

        from fixers import fix_progressive_disclosure
        from models import LintResult

        fix_progressive_disclosure(skill_dir, LintResult(rule_id=14, severity=Severity.WARNING, message=""))

        # SKILL.md no longer has 4-backtick fences
        skill_text = (skill_dir / "SKILL.md").read_text()
        assert "````" not in skill_text
        assert "references/fix-templates.md" in skill_text

        # references/fix-templates.md now exists and contains the extracted content
        tmpl = skill_dir / "references" / "fix-templates.md"
        assert tmpl.is_file()
        assert "````" in tmpl.read_text()

        # Re-lint: rule 14 no longer fires
        results = rules.check_progressive_disclosure(skill_dir)
        assert results == []


# ---------------------------------------------------------------------------
# Rule 15: Semantic reference-tier sections
# ---------------------------------------------------------------------------


class TestRule15:
    def test_detects_reference_tier_headings(self):
        results = rules.check_semantic_sections(FIXTURES / "semantic-sections")
        assert len(results) == 1
        r = results[0]
        assert r.rule_id == 15
        assert r.fixable is True
        assert "Troubleshooting" in r.message
        assert "Advanced" in r.message

    def test_clean_skill_passes(self):
        results = rules.check_semantic_sections(FIXTURES / "valid-skill")
        assert results == []

    def test_fix_routes_to_correct_reference_files(self, tmp_path):
        shutil.copytree(FIXTURES / "semantic-sections", tmp_path / "skill", dirs_exist_ok=True)
        skill_dir = tmp_path / "skill"

        from fixers import fix_semantic_sections
        from models import LintResult

        fix_semantic_sections(skill_dir, LintResult(rule_id=15, severity=Severity.WARNING, message=""))

        skill_text = (skill_dir / "SKILL.md").read_text()
        assert "references/troubleshooting.md" in skill_text
        assert "references/advanced.md" in skill_text
        assert (skill_dir / "references" / "troubleshooting.md").is_file()
        assert (skill_dir / "references" / "advanced.md").is_file()

        # Re-lint: rule 15 no longer fires
        assert rules.check_semantic_sections(skill_dir) == []


# ---------------------------------------------------------------------------
# Rule 14 — additional edge cases
# ---------------------------------------------------------------------------


@pytest.fixture()
def dense_skill(tmp_path) -> Path:
    skill_dir = tmp_path / "skill"
    shutil.copytree(FIXTURES / "dense-skill", skill_dir, dirs_exist_ok=True)
    return skill_dir


def test_rule14_fix_idempotent(dense_skill):
    """Calling the fixer twice must not duplicate content in references/."""
    from fixers import fix_progressive_disclosure
    from models import LintResult

    skill_dir = dense_skill
    stub = LintResult(rule_id=14, severity=Severity.WARNING, message="")

    fix_progressive_disclosure(skill_dir, stub)
    after_first = (skill_dir / "references" / "fix-templates.md").read_text()

    fix_progressive_disclosure(skill_dir, stub)  # no 4-backtick fences remain
    after_second = (skill_dir / "references" / "fix-templates.md").read_text()

    assert after_first == after_second


def test_rule14_fix_appends_to_existing_references(dense_skill):
    """Fixer must append to an existing references/fix-templates.md, not overwrite."""
    from fixers import fix_progressive_disclosure
    from models import LintResult

    skill_dir = dense_skill
    refs_dir = skill_dir / "references"
    refs_dir.mkdir()
    prior = "# Fix Templates\n\nPrior content.\n"
    (refs_dir / "fix-templates.md").write_text(prior)

    fix_progressive_disclosure(skill_dir, LintResult(rule_id=14, severity=Severity.WARNING, message=""))

    result = (refs_dir / "fix-templates.md").read_text()
    assert "Prior content." in result
    assert "````" in result  # newly extracted template appended


def test_rule14_multiple_template_sections(tmp_path):
    """All 4-backtick sections are extracted, not just the first."""
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: t\ndescription: Use when.\nmetadata:\n  author: T\n---\n\n"
        "## Templates A\n\n````markdown\n# A\n````\n\n"
        "## Templates B\n\n````markdown\n# B\n````\n",
        encoding="utf-8",
    )

    results = rules.check_progressive_disclosure(skill_dir)
    assert len(results) == 1
    assert "Templates A" in results[0].message
    assert "Templates B" in results[0].message

    from fixers import fix_progressive_disclosure
    fix_progressive_disclosure(skill_dir, results[0])

    skill_text = (skill_dir / "SKILL.md").read_text()
    assert "````" not in skill_text
    tmpl_text = (skill_dir / "references" / "fix-templates.md").read_text()
    assert "# A" in tmpl_text
    assert "# B" in tmpl_text


# ---------------------------------------------------------------------------
# Rule 15 — additional edge cases
# ---------------------------------------------------------------------------


@pytest.fixture()
def semantic_skill(tmp_path) -> Path:
    skill_dir = tmp_path / "skill"
    shutil.copytree(FIXTURES / "semantic-sections", skill_dir, dirs_exist_ok=True)
    return skill_dir


def test_rule15_fix_idempotent(semantic_skill):
    """Calling the fixer twice must not duplicate content in references/."""
    from fixers import fix_semantic_sections
    from models import LintResult

    skill_dir = semantic_skill
    stub = LintResult(rule_id=15, severity=Severity.WARNING, message="")

    fix_semantic_sections(skill_dir, stub)
    ts_after_first = (skill_dir / "references" / "troubleshooting.md").read_text()

    fix_semantic_sections(skill_dir, stub)  # sections are now pointers — no-op
    ts_after_second = (skill_dir / "references" / "troubleshooting.md").read_text()

    assert ts_after_first == ts_after_second


def test_rule15_fix_appends_to_existing_references(semantic_skill):
    """Fixer must append to a pre-existing references/ file, not overwrite it."""
    from fixers import fix_semantic_sections
    from models import LintResult

    skill_dir = semantic_skill
    refs_dir = skill_dir / "references"
    refs_dir.mkdir()
    prior = "# Troubleshooting\n\nExisting guidance.\n"
    (refs_dir / "troubleshooting.md").write_text(prior)

    fix_semantic_sections(skill_dir, LintResult(rule_id=15, severity=Severity.WARNING, message=""))

    result = (refs_dir / "troubleshooting.md").read_text()
    assert "Existing guidance." in result
    assert "Error A" in result  # newly extracted content appended


def test_rule15_two_sections_same_target(tmp_path):
    """Troubleshooting and FAQ both route to troubleshooting.md."""
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: t\ndescription: Use when.\nmetadata:\n  author: T\n---\n\n"
        "## Troubleshooting\n\nCheck logs.\n\n"
        "## FAQ\n\nQ: Why? A: Because.\n",
        encoding="utf-8",
    )

    results = rules.check_semantic_sections(skill_dir)
    assert len(results) == 1
    assert "Troubleshooting" in results[0].message
    assert "FAQ" in results[0].message

    from fixers import fix_semantic_sections
    fix_semantic_sections(skill_dir, results[0])

    ts = skill_dir / "references" / "troubleshooting.md"
    assert ts.is_file()
    assert not (skill_dir / "references" / "faq.md").is_file()  # same target file
    ts_text = ts.read_text()
    assert "Check logs." in ts_text
    assert "Why?" in ts_text


def test_rule15_pointer_section_not_reflagged(tmp_path):
    """A section already replaced with a pointer must not trigger the rule."""
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: t\ndescription: Use when.\nmetadata:\n  author: T\n---\n\n"
        "## Troubleshooting\n\n> See `references/troubleshooting.md`.\n",
        encoding="utf-8",
    )
    assert rules.check_semantic_sections(skill_dir) == []


# ---------------------------------------------------------------------------
# Rule 17: Skill isolation
# ---------------------------------------------------------------------------

class TestRule17:
    def _make_skill(self, path: Path) -> None:
        (path / "SKILL.md").write_text(
            "---\nname: t\ndescription: Use when.\n---\n\n# T\n",
            encoding="utf-8",
        )

    def test_no_git_no_flag(self, tmp_path):
        """Skill not at repo root — rule should not fire."""
        self._make_skill(tmp_path)
        results = rules.check_skill_isolation(tmp_path)
        assert results == []

    def test_git_no_artifacts_no_flag(self, tmp_path):
        """Repo root with no non-skill artifacts — should not flag."""
        (tmp_path / ".git").mkdir()
        self._make_skill(tmp_path)
        results = rules.check_skill_isolation(tmp_path)
        assert results == []

    def test_flags_human_artifacts(self, tmp_path):
        """README and LICENSE at repo root should trigger the rule."""
        (tmp_path / ".git").mkdir()
        self._make_skill(tmp_path)
        (tmp_path / "README.md").write_text("# hi", encoding="utf-8")
        (tmp_path / "LICENSE").write_text("MIT", encoding="utf-8")
        results = rules.check_skill_isolation(tmp_path)
        assert len(results) == 1
        assert "README.md" in results[0].message
        assert "LICENSE" in results[0].message

    def test_flags_dev_artifacts(self, tmp_path):
        """pyproject.toml and src/ at repo root should trigger the rule."""
        (tmp_path / ".git").mkdir()
        self._make_skill(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[project]", encoding="utf-8")
        (tmp_path / "src").mkdir()
        results = rules.check_skill_isolation(tmp_path)
        assert len(results) == 1
        assert "pyproject.toml" in results[0].message
        assert "src/" in results[0].message

    def test_flags_lock_file(self, tmp_path):
        """Any *.lock file at repo root should trigger the rule."""
        (tmp_path / ".git").mkdir()
        self._make_skill(tmp_path)
        (tmp_path / "uv.lock").write_text("", encoding="utf-8")
        results = rules.check_skill_isolation(tmp_path)
        assert len(results) == 1
        assert "uv.lock" in results[0].message

    def test_message_mentions_skill_dirs(self, tmp_path):
        """Message should tell users to also move references/, scripts/, assets/."""
        (tmp_path / ".git").mkdir()
        self._make_skill(tmp_path)
        (tmp_path / "README.md").write_text("# hi", encoding="utf-8")
        results = rules.check_skill_isolation(tmp_path)
        assert "references/" in results[0].message
        assert "scripts/" in results[0].message
        assert "assets/" in results[0].message

    def test_severity_is_info(self, tmp_path):
        (tmp_path / ".git").mkdir()
        self._make_skill(tmp_path)
        (tmp_path / "README.md").write_text("# hi", encoding="utf-8")
        results = rules.check_skill_isolation(tmp_path)
        assert results[0].severity == Severity.INFO
        assert results[0].fixable is False


# ---------------------------------------------------------------------------
# Rule 19: README-tier sections in SKILL.md
# ---------------------------------------------------------------------------


class TestRule19:
    def _make_skill(self, tmp_path: Path, extra_sections: str) -> None:
        (tmp_path / "SKILL.md").write_text(
            f"---\nname: t\ndescription: Use when.\nmetadata:\n  author: T\n---\n\n"
            f"## Triage\n\nDo the thing.\n\n{extra_sections}",
            encoding="utf-8",
        )

    def test_installation_flagged(self, tmp_path):
        self._make_skill(tmp_path, "## Installation\n\nnpx skills add foo\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert len(results) == 1
        assert results[0].rule_id == 19
        assert results[0].severity == Severity.WARNING
        assert "Installation" in results[0].message

    def test_features_flagged(self, tmp_path):
        self._make_skill(tmp_path, "## Features\n\n- feature 1\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert len(results) == 1

    def test_getting_started_flagged(self, tmp_path):
        self._make_skill(tmp_path, "## Getting Started\n\nRun X first.\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert len(results) == 1
        assert "Getting Started" in results[0].message

    def test_prerequisites_flagged(self, tmp_path):
        self._make_skill(tmp_path, "## Prerequisites\n\nNeed Python 3.12.\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert len(results) == 1

    def test_quick_start_flagged(self, tmp_path):
        self._make_skill(tmp_path, "## Quick Start\n\nRun the tool.\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert len(results) == 1

    def test_changelog_flagged(self, tmp_path):
        self._make_skill(tmp_path, "## Changelog\n\n- v1.0 release\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert len(results) == 1

    def test_requirements_flagged(self, tmp_path):
        self._make_skill(tmp_path, "## Requirements\n\nPython 3.12+.\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert len(results) == 1

    def test_overview_not_flagged(self, tmp_path):
        self._make_skill(tmp_path, "## Overview\n\nBrief context.\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert results == []

    def test_introduction_not_flagged(self, tmp_path):
        self._make_skill(tmp_path, "## Introduction\n\nContext here.\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert results == []

    def test_setup_flagged(self, tmp_path):
        self._make_skill(tmp_path, "## Setup\n\nConfigure env vars.\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert len(results) == 1

    def test_release_notes_flagged(self, tmp_path):
        self._make_skill(tmp_path, "## Release Notes\n\n- v1.1 added X\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert len(results) == 1

    def test_uninstall_not_flagged(self, tmp_path):
        # "Uninstall" must not match because keyword is not at heading start
        self._make_skill(tmp_path, "## Uninstall old version\n\nRemove cache.\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert results == []

    def test_compound_heading_not_flagged(self, tmp_path):
        # "Input Requirements" — keyword is not at start, must not fire
        self._make_skill(tmp_path, "## Input Requirements\n\nContext.\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert results == []

    def test_feature_flags_flagged(self, tmp_path):
        # "Feature Flags" leads with a README-tier keyword — should fire
        self._make_skill(tmp_path, "## Feature Flags\n\nContext.\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert len(results) == 1

    def test_h3_not_flagged(self, tmp_path):
        # Only H2 headings are scanned, consistent with Rules 15/16
        self._make_skill(tmp_path, "## How to Use\n\n### Installation\n\nSub-step.\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert results == []

    def test_multiple_violations_single_result(self, tmp_path):
        self._make_skill(tmp_path, "## Installation\n\nfoo\n\n## Features\n\nbar\n")
        results = rules.check_readme_tier_in_skill(tmp_path)
        assert len(results) == 1
        assert "Installation" in results[0].message
        assert "Features" in results[0].message

    def test_valid_skill_passes(self):
        results = rules.check_readme_tier_in_skill(FIXTURES / "valid-skill")
        assert results == []


class TestRule20:
    """Rule 20: triage workflow with 3+ steps must include at least one semantic step."""

    def _make_skill(self, tmp_path: Path, body: str) -> None:
        (tmp_path / "SKILL.md").write_text(
            "---\nname: t\ndescription: Use when.\nmetadata:\n  author: T\n---\n\n"
            + body,
            encoding="utf-8",
        )

    def test_command_only_workflow_flagged(self):
        """Fixture: 3 steps, all commands — should flag."""
        results = rules.check_triage_semantic_balance(FIXTURES / "command-only-workflow")
        assert len(results) == 1
        assert results[0].rule_id == 20
        assert results[0].severity == Severity.INFO

    def test_workflow_with_ask_step_passes(self, tmp_path):
        """3 steps where one contains 'Ask:' — should pass."""
        self._make_skill(
            tmp_path,
            "## Triage\n\n"
            "### Step 1 — Run\n\n```bash\ntool check .\n```\n\n"
            "### Step 2 — Fix\n\n```bash\ntool --fix\n```\n\n"
            "### Step 3 — Review\n\nAsk: does the description route correctly?\n",
        )
        results = rules.check_triage_semantic_balance(tmp_path)
        assert results == []

    def test_workflow_with_read_and_ask_passes(self, tmp_path):
        """'Read X and ask' phrasing — should pass."""
        self._make_skill(
            tmp_path,
            "## Triage\n\n"
            "### Step 1 — Lint\n\n```bash\ntool .\n```\n\n"
            "### Step 2 — Fix\n\nApply suggested fixes.\n\n"
            "### Step 3 — Semantic\n\nRead the description and ask: is it a routing signal?\n",
        )
        results = rules.check_triage_semantic_balance(tmp_path)
        assert results == []

    def test_fewer_than_threshold_not_flagged(self, tmp_path):
        """Fewer than 3 step headings — rule does not fire."""
        self._make_skill(
            tmp_path,
            "## Triage\n\n"
            "### Step 1 — Run\n\n```bash\ntool .\n```\n\n"
            "### Step 2 — Fix\n\nApply fixes.\n",
        )
        results = rules.check_triage_semantic_balance(tmp_path)
        assert results == []

    def test_no_skill_md_returns_empty(self, tmp_path):
        results = rules.check_triage_semantic_balance(tmp_path)
        assert results == []

    def test_message_mentions_step_count(self):
        results = rules.check_triage_semantic_balance(FIXTURES / "command-only-workflow")
        assert "3" in results[0].message


class TestRule21:
    """Rule 21: Python entry-point scripts in scripts/ must declare deps via PEP 723."""

    def _write_script(self, scripts_dir: Path, name: str, content: str) -> None:
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (scripts_dir / name).write_text(content, encoding="utf-8")

    def test_entry_point_without_pep723_flagged(self):
        """Fixture: shebang present, no # /// script block — should flag."""
        results = rules.check_pep723_entry_points(FIXTURES / "no-pep723")
        assert len(results) == 1
        assert results[0].rule_id == 21
        assert results[0].severity == Severity.WARNING
        assert "skill-lint.py" in results[0].message

    def test_entry_point_with_pep723_passes(self, tmp_path):
        """Shebang + # /// script block — should pass."""
        self._write_script(
            tmp_path / "scripts",
            "skill-lint.py",
            "#!/usr/bin/env -S uv run\n# /// script\n# requires-python = '>=3.12'\n# ///\nimport sys\n",
        )
        results = rules.check_pep723_entry_points(tmp_path)
        assert results == []

    def test_module_without_shebang_not_flagged(self, tmp_path):
        """Module file (no shebang) is not an entry point — must not flag."""
        self._write_script(
            tmp_path / "scripts",
            "models.py",
            "from dataclasses import dataclass\n",
        )
        results = rules.check_pep723_entry_points(tmp_path)
        assert results == []

    def test_no_scripts_dir_returns_empty(self, tmp_path):
        results = rules.check_pep723_entry_points(tmp_path)
        assert results == []

    def test_multiple_violations_reported_together(self, tmp_path):
        """Two entry points without PEP 723 — both named in a single result."""
        for name in ("tool-a.py", "tool-b.py"):
            self._write_script(tmp_path / "scripts", name, "#!/usr/bin/env python3\npass\n")
        results = rules.check_pep723_entry_points(tmp_path)
        assert len(results) == 1
        assert "tool-a.py" in results[0].message
        assert "tool-b.py" in results[0].message

    def test_valid_skill_passes(self):
        results = rules.check_pep723_entry_points(FIXTURES / "valid-skill")
        assert results == []
