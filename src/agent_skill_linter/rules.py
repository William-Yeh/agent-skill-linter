"""All 10 lint rule implementations."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import yaml

from agent_skill_linter.models import LintResult, Severity

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str | None:
    """Read file text or return None if missing."""
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None


def _parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter from markdown text."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    try:
        return yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}


def _body_after_frontmatter(text: str) -> str:
    """Return the markdown body after YAML frontmatter."""
    match = re.match(r"^---\s*\n.*?\n---\s*\n?", text, re.DOTALL)
    if match:
        return text[match.end():]
    return text


# ---------------------------------------------------------------------------
# Rule 1: SKILL.md spec compliance (via skills-ref)
# ---------------------------------------------------------------------------

def check_spec_compliance(skill_dir: Path) -> list[LintResult]:
    from skills_ref import validate

    errors = validate(skill_dir)
    return [
        LintResult(
            rule_id=1,
            severity=Severity.ERROR,
            message=err,
            file="SKILL.md",
        )
        for err in errors
    ]


# ---------------------------------------------------------------------------
# Rule 2: LICENSE exists, Apache-2.0 or MIT, current year
# ---------------------------------------------------------------------------

_APACHE_MARKER = "Apache License"
_MIT_MARKER = "MIT License"


def check_license(skill_dir: Path) -> list[LintResult]:
    results: list[LintResult] = []
    lic = _read_text(skill_dir / "LICENSE")

    if lic is None:
        results.append(LintResult(
            rule_id=2,
            severity=Severity.WARNING,
            message="LICENSE file is missing.",
            fixable=True,
            file="LICENSE",
        ))
        return results

    is_apache = _APACHE_MARKER in lic
    is_mit = _MIT_MARKER in lic
    if not (is_apache or is_mit):
        results.append(LintResult(
            rule_id=2,
            severity=Severity.WARNING,
            message="LICENSE is not Apache-2.0 or MIT.",
            file="LICENSE",
        ))

    current_year = str(datetime.now().year)
    if current_year not in lic:
        results.append(LintResult(
            rule_id=2,
            severity=Severity.WARNING,
            message=f"LICENSE does not contain the current year ({current_year}).",
            fixable=True,
            file="LICENSE",
        ))

    return results


# ---------------------------------------------------------------------------
# Rule 3: metadata.author in SKILL.md frontmatter
# ---------------------------------------------------------------------------

def check_author(skill_dir: Path) -> list[LintResult]:
    text = _read_text(skill_dir / "SKILL.md")
    if text is None:
        return []  # Rule 1 already flags missing SKILL.md

    fm = _parse_frontmatter(text)
    metadata = fm.get("metadata", {}) or {}
    if not metadata.get("author"):
        return [LintResult(
            rule_id=3,
            severity=Severity.WARNING,
            message="SKILL.md frontmatter is missing metadata.author.",
            fixable=True,
            file="SKILL.md",
        )]
    return []


# ---------------------------------------------------------------------------
# Rule 4: README badges (CI, license, Agent Skills)
# ---------------------------------------------------------------------------

_BADGE_PATTERNS = [
    (r"!\[.*?CI.*?\]", "CI status badge"),
    (r"!\[.*?[Ll]icense.*?\]", "License badge"),
    (r"!\[.*?[Aa]gent\s*[Ss]kills.*?\]", "Agent Skills badge"),
]


def check_readme_badges(skill_dir: Path) -> list[LintResult]:
    text = _read_text(skill_dir / "README.md")
    if text is None:
        return [LintResult(
            rule_id=4,
            severity=Severity.WARNING,
            message="README.md is missing.",
            fixable=True,
            file="README.md",
        )]

    results: list[LintResult] = []
    for pattern, desc in _BADGE_PATTERNS:
        if not re.search(pattern, text):
            results.append(LintResult(
                rule_id=4,
                severity=Severity.WARNING,
                message=f"README.md is missing {desc}.",
                fixable=True,
                file="README.md",
            ))
    return results


# ---------------------------------------------------------------------------
# Rule 5: .github/workflows/ has CI workflow
# ---------------------------------------------------------------------------

def check_ci_workflow(skill_dir: Path) -> list[LintResult]:
    wf_dir = skill_dir / ".github" / "workflows"
    if not wf_dir.is_dir():
        return [LintResult(
            rule_id=5,
            severity=Severity.WARNING,
            message="No .github/workflows/ directory found.",
            fixable=True,
            file=".github/workflows/ci.yml",
        )]

    yamls = list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml"))
    if not yamls:
        return [LintResult(
            rule_id=5,
            severity=Severity.WARNING,
            message="No CI workflow files in .github/workflows/.",
            fixable=True,
            file=".github/workflows/ci.yml",
        )]
    return []


# ---------------------------------------------------------------------------
# Rule 6: README has Installation section
# ---------------------------------------------------------------------------

def check_installation_section(skill_dir: Path) -> list[LintResult]:
    text = _read_text(skill_dir / "README.md")
    if text is None:
        return []  # Rule 4 already flags missing README

    if not re.search(r"^#{1,3}\s+.*[Ii]nstall", text, re.MULTILINE):
        return [LintResult(
            rule_id=6,
            severity=Severity.WARNING,
            message="README.md is missing an Installation section.",
            fixable=True,
            file="README.md",
        )]
    return []


# ---------------------------------------------------------------------------
# Rule 7: README has Usage section with starter prompts
# ---------------------------------------------------------------------------

def check_usage_section(skill_dir: Path) -> list[LintResult]:
    text = _read_text(skill_dir / "README.md")
    if text is None:
        return []  # Rule 4 already flags missing README

    if not re.search(r"^#{1,3}\s+.*[Uu]sage", text, re.MULTILINE):
        return [LintResult(
            rule_id=7,
            severity=Severity.WARNING,
            message="README.md is missing a Usage section.",
            fixable=True,
            file="README.md",
        )]
    return []


# ---------------------------------------------------------------------------
# Rule 8: Content dedup between README.md and SKILL.md
# ---------------------------------------------------------------------------

_DEDUP_THRESHOLD = 0.5  # warn if >50% of SKILL.md body lines also appear in README


def check_content_dedup(skill_dir: Path) -> list[LintResult]:
    skill_text = _read_text(skill_dir / "SKILL.md")
    readme_text = _read_text(skill_dir / "README.md")
    if skill_text is None or readme_text is None:
        return []

    skill_body = _body_after_frontmatter(skill_text)
    skill_lines = {line.strip() for line in skill_body.splitlines() if len(line.strip()) > 20}
    if not skill_lines:
        return []

    readme_set = {line.strip() for line in readme_text.splitlines()}
    overlap = skill_lines & readme_set

    ratio = len(overlap) / len(skill_lines)
    if ratio > _DEDUP_THRESHOLD:
        return [LintResult(
            rule_id=8,
            severity=Severity.INFO,
            message=(
                f"{len(overlap)}/{len(skill_lines)} non-trivial SKILL.md body lines "
                f"also appear in README.md ({ratio:.0%} overlap). "
                "Consider making SKILL.md agent-focused and README.md human-focused."
            ),
        )]
    return []


# ---------------------------------------------------------------------------
# Rule 9: SKILL.md body < 500 lines
# ---------------------------------------------------------------------------

_MAX_BODY_LINES = 500


def check_skill_body_length(skill_dir: Path) -> list[LintResult]:
    text = _read_text(skill_dir / "SKILL.md")
    if text is None:
        return []

    body = _body_after_frontmatter(text)
    line_count = len(body.splitlines())
    if line_count > _MAX_BODY_LINES:
        return [LintResult(
            rule_id=9,
            severity=Severity.INFO,
            message=(
                f"SKILL.md body is {line_count} lines (limit: {_MAX_BODY_LINES}). "
                "Large skills may exceed agent context windows."
            ),
            file="SKILL.md",
        )]
    return []


# ---------------------------------------------------------------------------
# Rule 10: Non-standard directories flagged
# ---------------------------------------------------------------------------

_STANDARD_DIRS = {
    "scripts", "references", "assets",
    ".github", ".git", ".venv", "__pycache__",
    "src", "tests", "test", "node_modules",
}


def check_nonstandard_dirs(skill_dir: Path) -> list[LintResult]:
    results: list[LintResult] = []
    for entry in sorted(skill_dir.iterdir()):
        if entry.is_dir() and entry.name not in _STANDARD_DIRS and not entry.name.startswith("."):
            results.append(LintResult(
                rule_id=10,
                severity=Severity.INFO,
                message=(
                    f"Non-standard directory '{entry.name}/'. "
                    "Recommended: scripts/, references/, assets/."
                ),
            ))
    return results
