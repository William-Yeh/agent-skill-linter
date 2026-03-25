"""Tests for all lint rules."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

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
# Rule 12: CSO name
# ---------------------------------------------------------------------------


class TestRule12:
    def test_noun_form_name(self, tmp_path):
        (tmp_path / "SKILL.md").write_text(
            "---\nname: pdf-processor\ndescription: Use when working with PDFs.\n---\n\n# Body\n"
        )
        results = rules.check_cso_name(tmp_path)
        assert len(results) == 1
        assert results[0].severity == Severity.INFO
        assert "pdf-processor" in results[0].message

    def test_gerund_name(self, tmp_path):
        (tmp_path / "SKILL.md").write_text(
            "---\nname: processing-pdfs\ndescription: Use when working with PDFs.\n---\n\n# Body\n"
        )
        results = rules.check_cso_name(tmp_path)
        assert results == []

    def test_gerund_suffix(self, tmp_path):
        (tmp_path / "SKILL.md").write_text(
            "---\nname: condition-based-waiting\ndescription: Use when tests are flaky.\n---\n\n# Body\n"
        )
        results = rules.check_cso_name(tmp_path)
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

        from agent_skill_linter.fixers import fix_ci_workflow
        from agent_skill_linter.models import LintResult

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

        from agent_skill_linter.fixers import fix_progressive_disclosure
        from agent_skill_linter.models import LintResult

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

        from agent_skill_linter.fixers import fix_semantic_sections
        from agent_skill_linter.models import LintResult

        fix_semantic_sections(skill_dir, LintResult(rule_id=15, severity=Severity.WARNING, message=""))

        skill_text = (skill_dir / "SKILL.md").read_text()
        assert "references/troubleshooting.md" in skill_text
        assert "references/advanced.md" in skill_text
        assert (skill_dir / "references" / "troubleshooting.md").is_file()
        assert (skill_dir / "references" / "advanced.md").is_file()

        # Re-lint: rule 15 no longer fires
        assert rules.check_semantic_sections(skill_dir) == []


# ---------------------------------------------------------------------------
# Rule 16: Heavy step-conditional sections
# ---------------------------------------------------------------------------


def _make_step_skill(tmp_path, step_lines: int) -> Path:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    body_lines = "\n".join(f"- detail line {i}" for i in range(step_lines))
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: step-skill\ndescription: Use when testing.\nmetadata:\n  author: T\n---\n\n"
        f"## Quick Start\n\nRun the tool.\n\n"
        f"## Step 2 — Apply fixes\n\n{body_lines}\n",
        encoding="utf-8",
    )
    return skill_dir


class TestRule16:
    def test_detects_heavy_step_section(self, tmp_path):
        skill_dir = _make_step_skill(tmp_path, step_lines=35)
        results = rules.check_step_conditional_sections(skill_dir)
        assert len(results) == 1
        r = results[0]
        assert r.rule_id == 16
        assert r.fixable is False
        assert "Step 2" in r.message

    def test_short_step_section_passes(self, tmp_path):
        skill_dir = _make_step_skill(tmp_path, step_lines=10)
        results = rules.check_step_conditional_sections(skill_dir)
        assert results == []

    def test_non_step_heading_not_flagged(self):
        results = rules.check_step_conditional_sections(FIXTURES / "valid-skill")
        assert results == []


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
    from agent_skill_linter.fixers import fix_progressive_disclosure
    from agent_skill_linter.models import LintResult

    skill_dir = dense_skill
    stub = LintResult(rule_id=14, severity=Severity.WARNING, message="")

    fix_progressive_disclosure(skill_dir, stub)
    after_first = (skill_dir / "references" / "fix-templates.md").read_text()

    fix_progressive_disclosure(skill_dir, stub)  # no 4-backtick fences remain
    after_second = (skill_dir / "references" / "fix-templates.md").read_text()

    assert after_first == after_second


def test_rule14_fix_appends_to_existing_references(dense_skill):
    """Fixer must append to an existing references/fix-templates.md, not overwrite."""
    from agent_skill_linter.fixers import fix_progressive_disclosure
    from agent_skill_linter.models import LintResult

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

    from agent_skill_linter.fixers import fix_progressive_disclosure
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
    from agent_skill_linter.fixers import fix_semantic_sections
    from agent_skill_linter.models import LintResult

    skill_dir = semantic_skill
    stub = LintResult(rule_id=15, severity=Severity.WARNING, message="")

    fix_semantic_sections(skill_dir, stub)
    ts_after_first = (skill_dir / "references" / "troubleshooting.md").read_text()

    fix_semantic_sections(skill_dir, stub)  # sections are now pointers — no-op
    ts_after_second = (skill_dir / "references" / "troubleshooting.md").read_text()

    assert ts_after_first == ts_after_second


def test_rule15_fix_appends_to_existing_references(semantic_skill):
    """Fixer must append to a pre-existing references/ file, not overwrite it."""
    from agent_skill_linter.fixers import fix_semantic_sections
    from agent_skill_linter.models import LintResult

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

    from agent_skill_linter.fixers import fix_semantic_sections
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
# Rule 16 — additional edge cases
# ---------------------------------------------------------------------------


def test_rule16_exactly_at_threshold_passes(tmp_path):
    """A step section of exactly 30 lines must not trigger (threshold is >30).

    The section body includes the heading line + blank line, so 28 detail
    lines yield a 30-line section total — right at the threshold, not over.
    """
    skill_dir = _make_step_skill(tmp_path, step_lines=28)
    assert rules.check_step_conditional_sections(skill_dir) == []


def test_rule16_phase_heading_detected(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    body = "\n".join(f"- item {i}" for i in range(35))
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: t\ndescription: Use when.\nmetadata:\n  author: T\n---\n\n"
        f"## Phase 2 — Deploy\n\n{body}\n",
        encoding="utf-8",
    )
    results = rules.check_step_conditional_sections(skill_dir)
    assert len(results) == 1
    assert "Phase 2" in results[0].message


def test_rule16_numbered_heading_detected(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    body = "\n".join(f"- item {i}" for i in range(35))
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: t\ndescription: Use when.\nmetadata:\n  author: T\n---\n\n"
        f"## 3. Apply fixes\n\n{body}\n",
        encoding="utf-8",
    )
    results = rules.check_step_conditional_sections(skill_dir)
    assert len(results) == 1
    assert "3." in results[0].message


def test_rule16_after_heading_detected(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    body = "\n".join(f"- item {i}" for i in range(35))
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: t\ndescription: Use when.\nmetadata:\n  author: T\n---\n\n"
        f"## After running the scan\n\n{body}\n",
        encoding="utf-8",
    )
    results = rules.check_step_conditional_sections(skill_dir)
    assert len(results) == 1
    assert "After running" in results[0].message


def test_rule16_once_heading_detected(tmp_path):
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    body = "\n".join(f"- item {i}" for i in range(35))
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: t\ndescription: Use when.\nmetadata:\n  author: T\n---\n\n"
        f"## Once complete\n\n{body}\n",
        encoding="utf-8",
    )
    results = rules.check_step_conditional_sections(skill_dir)
    assert len(results) == 1
    assert "Once complete" in results[0].message
