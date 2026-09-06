"""End-to-end tests for the `check` command, driven through click's CliRunner.

The script file is `skill-lint.py` (hyphenated), so it is loaded by path rather
than imported by name.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

FIXTURES = Path(__file__).parent / "fixtures"
SCRIPT = Path(__file__).parent.parent / "skill" / "scripts" / "skill-lint.py"


@pytest.fixture(scope="module")
def cli():
    spec = importlib.util.spec_from_file_location("skill_lint", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main


def _subdir_repo(tmp_path: Path) -> Path:
    """Copy the subdir-layout fixture and mark its root with a real .git plus dev artifacts."""
    root = tmp_path / "repo"
    shutil.copytree(FIXTURES / "valid-skill-subdir", root)
    (root / ".git").mkdir()
    (root / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (root / "tests").mkdir()
    return root


class TestCheckOnRepoRoot:
    def test_subdir_layout_from_root_passes(self, cli, tmp_path):
        """`check <repo-root>` on a skill/ layout lints skill/: no Rule 1 "missing
        SKILL.md" error and no Rule 17 "move it into skill/" info."""
        root = _subdir_repo(tmp_path)
        result = CliRunner().invoke(cli, ["check", str(root), "--format", "json"])
        assert result.exit_code == 0, result.output
        findings = json.loads(result.stdout)
        assert [f for f in findings if f["rule"] in (1, 17)] == []

    def test_redirect_is_announced_on_stderr_only(self, cli, tmp_path):
        root = _subdir_repo(tmp_path)
        result = CliRunner().invoke(cli, ["check", str(root), "--format", "json"])
        assert str((root / "skill").resolve()) in result.stderr
        json.loads(result.stdout)  # stdout stays machine-readable

    def test_root_layout_is_not_redirected(self, cli):
        result = CliRunner().invoke(
            cli, ["check", str(FIXTURES / "valid-skill"), "--format", "json"]
        )
        assert result.exit_code == 0, result.output
        assert result.stderr == ""
