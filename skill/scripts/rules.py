"""All lint rule implementations."""

from __future__ import annotations

import ast
import json
import re
import sys
import tomllib
from datetime import datetime
from pathlib import Path

import yaml

from models import LintResult, Severity

PLUGIN_MANIFEST_RELPATH = Path(".claude-plugin") / "plugin.json"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str | None:
    """Read file text or return None if missing."""
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None


def _repo_root(skill_dir: Path) -> Path:
    """Walk up from skill_dir to find the repo or plugin root; return skill_dir if none found.

    Recognises:
    - `.git` (real git repo)
    - `.gitroot` (test fixture marker, since git cannot track files named .git
      inside subdirectories)
    - `.claude-plugin/plugin.json` (plugin manifest — establishes the plugin
      root regardless of git initialization state)
    """
    for candidate in [skill_dir, *skill_dir.parents]:
        if (
            (candidate / ".git").exists()
            or (candidate / ".gitroot").exists()
            or (candidate / PLUGIN_MANIFEST_RELPATH).is_file()
        ):
            return candidate
    return skill_dir


def _is_plugin_root(path: Path) -> bool:
    """Return True if `path` has the plugin manifest at the conventional location."""
    return (path / PLUGIN_MANIFEST_RELPATH).is_file()


def _repo_path(skill_dir: Path, name: str) -> Path:
    """Return path to a repo-level file or dir, preferring skill_dir then repo root."""
    candidate = skill_dir / name
    if candidate.exists():
        return candidate
    return _repo_root(skill_dir) / name


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


def _extract_section_content(text: str, heading_pattern: str) -> str | None:
    """Return the body of the first matching section (up to the next equal/higher heading)."""
    m = re.search(heading_pattern, text, re.MULTILINE)
    if not m:
        return None
    level = len(re.match(r"^(#+)", m.group()).group(1))
    rest = text[m.end():]
    end = re.search(rf"^#{{1,{level}}}\s", rest, re.MULTILINE)
    return rest[: end.start()] if end else rest


# ---------------------------------------------------------------------------
# Rule 1: SKILL.md spec compliance (via skills-ref)
# ---------------------------------------------------------------------------

def check_spec_compliance(skill_dir: Path) -> list[LintResult]:
    from skills_ref import validate
    from skills_ref.validator import validate_metadata
    from skills_ref.parser import find_skill_md, parse_frontmatter
    from skills_ref.errors import ParseError

    # When skill_dir is a subdir (not the repo root), skip the dir-name-match
    # check: the installed directory name comes from SKILL.md 'name', not the
    # source directory name.
    if (skill_dir / ".git").exists():
        errors = validate(skill_dir)
    else:
        skill_md = find_skill_md(skill_dir)
        if skill_md is None:
            errors = ["Missing required file: SKILL.md"]
        else:
            try:
                content = skill_md.read_text(encoding="utf-8")
                metadata, _ = parse_frontmatter(content)
                errors = validate_metadata(metadata, skill_dir=None)
            except ParseError as e:
                errors = [str(e)]

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
    lic = _read_text(_repo_path(skill_dir, "LICENSE"))

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
    text = _read_text(_repo_path(skill_dir, "README.md"))
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
    wf_dir = _repo_path(skill_dir, ".github") / "workflows"
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
    text = _read_text(_repo_path(skill_dir, "README.md"))
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
# Rule 7: README has Usage section with starter prompts and CLI subsection
# ---------------------------------------------------------------------------

_USAGE_HEADING = r"^#{1,3}\s+.*[Uu]sage"


def check_usage_section(skill_dir: Path) -> list[LintResult]:
    text = _read_text(_repo_path(skill_dir, "README.md"))
    if text is None:
        return []  # Rule 4 already flags missing README

    if not re.search(_USAGE_HEADING, text, re.MULTILINE):
        return [LintResult(
            rule_id=7,
            severity=Severity.WARNING,
            message="README.md is missing a Usage section.",
            fixable=True,
            file="README.md",
        )]

    results: list[LintResult] = []
    section = _extract_section_content(text, _USAGE_HEADING)

    if section is not None and not re.search(r"-\s+`[^`]+`", section):
        results.append(LintResult(
            rule_id=7,
            severity=Severity.WARNING,
            message=(
                "README.md Usage section is missing starter prompt examples "
                "(e.g. - `Try this prompt`)."
            ),
            file="README.md",
        ))

    if section is not None and not re.search(r"^#{2,4}\s+.*CLI", section, re.MULTILINE | re.IGNORECASE):
        results.append(LintResult(
            rule_id=7,
            severity=Severity.INFO,
            message="README.md Usage section is missing a CLI usage subsection.",
            file="README.md",
        ))

    return results



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
    "skill", "skills",
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


# ---------------------------------------------------------------------------
# Rule 11: CSO — description starts with "Use when"
# ---------------------------------------------------------------------------

def check_cso_description(skill_dir: Path) -> list[LintResult]:
    text = _read_text(skill_dir / "SKILL.md")
    if text is None:
        return []

    fm = _parse_frontmatter(text)
    description = str(fm.get("description", "")).strip()
    if not description:
        return []

    if not description.startswith("Use when"):
        return [LintResult(
            rule_id=11,
            severity=Severity.WARNING,
            message=(
                "SKILL.md description should start with 'Use when...' "
                "(CSO: triggering conditions only, not workflow summary)."
            ),
            file="SKILL.md",
        )]
    return []




# ---------------------------------------------------------------------------
# Rule 13: Python invocation consistency
# ---------------------------------------------------------------------------

_SKIP_DIRS = frozenset({".venv", "node_modules", "__pycache__", ".git", ".pytest_cache"})
_BAD_PYTHON_RE = re.compile(r"^python3?\s+")
_HEREDOC_RE = re.compile(r"^python3?\s+-\s*<<")
_WRAPPED_RE = re.compile(r"^(uv|poetry|pipenv)\s+run\s+python")


def _uses_uv(skill_dir: Path) -> bool:
    """Return True if this skill (or its enclosing repo/plugin) is uv-managed."""
    root = _repo_root(skill_dir)
    for candidate in {skill_dir, root}:
        if (candidate / "uv.lock").is_file():
            return True
        text = _read_text(candidate / "pyproject.toml")
        if text and "uv_build" in text:
            return True
    return False


def _has_non_stdlib_deps(skill_dir: Path) -> bool:
    """Return True if pyproject.toml at skill_dir or repo root declares non-stdlib deps."""
    root = _repo_root(skill_dir)
    for candidate in {skill_dir, root}:
        text = _read_text(candidate / "pyproject.toml")
        if not text:
            continue
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError:
            continue
        if data.get("project", {}).get("dependencies"):
            return True
    return False


def _scan_markdown_for_bad_python(text: str) -> bool:
    """Return True if any bash code block contains a bare python/python3 invocation."""
    in_bash = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_bash:
                lang = stripped[3:].strip().lower()
                in_bash = lang in ("bash", "sh", "shell", "zsh", "")
            else:
                in_bash = False
            continue
        if not in_bash:
            continue
        if _BAD_PYTHON_RE.match(stripped) and not _HEREDOC_RE.match(stripped) and not _WRAPPED_RE.match(stripped):
            return True
    return False


def _scan_yaml_for_bad_python(text: str) -> bool:
    """Return True if any run step contains a bare python/python3 invocation."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        # Normalise "run: python3 ..." and "- run: python3 ..." to just the command
        candidate = re.sub(r"^-?\s*run:\s*", "", stripped) if re.match(r"^-?\s*run:\s*\S", stripped) else stripped
        if _BAD_PYTHON_RE.match(candidate) and not _HEREDOC_RE.match(candidate) and not _WRAPPED_RE.match(candidate):
            return True
    return False


_REFERENCE_TIER_RE = re.compile(
    r"\b(troubleshoot|faq|common[\s-]issue|background|architecture|how[\s-]it[\s-]works|"
    r"glossary|terminolog|advanced|edge[\s-]case|examples?|changelog|history)",
    re.IGNORECASE,
)


def check_semantic_sections(skill_dir: Path) -> list[LintResult]:
    """Rule 15: H2 sections with reference-tier headings belong in references/."""
    text = _read_text(skill_dir / "SKILL.md")
    if text is None:
        return []

    body = _body_after_frontmatter(text)
    headings = list(re.finditer(r"^## .+", body, re.MULTILINE))
    flagged = []
    for i, m in enumerate(headings):
        if not _REFERENCE_TIER_RE.search(m.group()):
            continue
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        section_body = body[m.end():end].strip()
        if re.match(r"^>\s+See\s+`references/", section_body):
            continue  # already a pointer — section was previously moved
        flagged.append(m.group().lstrip("# ").strip())
    if not flagged:
        return []

    names = ", ".join(f'"{s}"' for s in flagged)
    return [LintResult(
        rule_id=15,
        severity=Severity.WARNING,
        message=(
            f"SKILL.md has reference-tier sections: {names}. "
            "These are consulted reactively — move to references/."
        ),
        fixable=True,
        file="SKILL.md",
    )]



def check_progressive_disclosure(skill_dir: Path) -> list[LintResult]:
    """Rule 14: SKILL.md sections with 4-backtick fences should move to references/."""
    text = _read_text(skill_dir / "SKILL.md")
    if text is None:
        return []

    body = _body_after_frontmatter(text)
    headings = list(re.finditer(r"^## .+", body, re.MULTILINE))

    dense = []
    for i, m in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(body)
        section = body[m.start():end]
        if re.search(r"^`{4,}", section, re.MULTILINE):
            dense.append(m.group().lstrip("# ").strip())

    if not dense:
        return []

    names = ", ".join(f'"{s}"' for s in dense)
    return [LintResult(
        rule_id=14,
        severity=Severity.WARNING,
        message=(
            f"SKILL.md embeds template content in sections: {names}. "
            "Move to references/ so agents load it only when needed."
        ),
        fixable=True,
        file="SKILL.md",
    )]


def check_python_invocations(skill_dir: Path) -> list[LintResult]:
    """Rule 13: docs must use `uv run python` when project is uv-managed with non-stdlib deps."""
    if not _uses_uv(skill_dir) or not _has_non_stdlib_deps(skill_dir):
        return []

    results: list[LintResult] = []

    for md_file in sorted(skill_dir.rglob("*.md")):
        if any(part in _SKIP_DIRS for part in md_file.parts):
            continue
        text = _read_text(md_file)
        if text and _scan_markdown_for_bad_python(text):
            rel = str(md_file.relative_to(skill_dir))
            results.append(LintResult(
                rule_id=13,
                severity=Severity.WARNING,
                message=(
                    f"`{rel}` contains a bare `python`/`python3` invocation in a bash code block. "
                    "Use `uv run python` for uv-managed projects with non-stdlib dependencies."
                ),
                file=rel,
            ))

    # Only scan CI workflow files — other YAML (Docker Compose, Taskfiles, etc.)
    # uses different keys and would produce false positives.
    wf_dir = skill_dir / ".github" / "workflows"
    if wf_dir.is_dir():
        yml_files = sorted(list(wf_dir.glob("*.yml")) + list(wf_dir.glob("*.yaml")))
        for yml_file in yml_files:
            text = _read_text(yml_file)
            if text and _scan_yaml_for_bad_python(text):
                rel = str(yml_file.relative_to(skill_dir))
                results.append(LintResult(
                    rule_id=13,
                    severity=Severity.WARNING,
                    message=(
                        f"`{rel}` contains a bare `python`/`python3` invocation in a run step. "
                        "Use `uv run python` for uv-managed projects with non-stdlib dependencies."
                    ),
                    file=rel,
                ))

    return results


# ---------------------------------------------------------------------------
# Rule 17: Skill isolation — skill files mixed with non-skill artifacts at repo root
# ---------------------------------------------------------------------------

_NON_SKILL_FILES = {
    # human-facing docs
    "README.md", "README.rst", "README.txt", "README",
    "LICENSE", "LICENSE.md", "LICENSE.txt",
    "CHANGELOG.md", "CHANGELOG.rst", "CHANGELOG", "CHANGES.md", "HISTORY.md",
    "DESIGN.md", "DESIGN", "CONTRIBUTING.md", "CONTRIBUTING",
    "CODE_OF_CONDUCT.md", "SECURITY.md",
    # build / package manifests
    "pyproject.toml", "setup.py", "setup.cfg",
    "package.json", "package-lock.json", "yarn.lock",
    "Cargo.toml", "Cargo.lock",
    "go.mod", "go.sum",
    "Makefile", "CMakeLists.txt",
}

_NON_SKILL_DIRS = {"src", "tests", "test", "node_modules", "dist", "build"}


# ---------------------------------------------------------------------------
# Rule 19: Division of labor — README-tier sections in SKILL.md
# ---------------------------------------------------------------------------

# Anchored at start so "## Input Requirements" doesn't fire — only headings
# that *lead* with a README-tier keyword are flagged (e.g. "## Requirements").
# Note: "changelog" overlaps with _REFERENCE_TIER_RE (Rule 15); both rules fire
# for a Changelog section, but with different advice (README vs references/).
_README_TIER_RE = re.compile(
    r"^(install(?:ation)?|set[\s-]?up|getting[\s-]started|quick[\s-]?start|"
    r"prerequisites?|requirements?|features?|changelog|release[\s-]notes?)\b",
    re.IGNORECASE,
)


def check_readme_tier_in_skill(skill_dir: Path) -> list[LintResult]:
    """Rule 19: SKILL.md should not contain sections that belong in README."""
    text = _read_text(skill_dir / "SKILL.md")
    if text is None:
        return []

    body = _body_after_frontmatter(text)
    flagged = []
    for m in re.finditer(r"^## .+", body, re.MULTILINE):
        heading_text = m.group().lstrip("# ").strip()
        if _README_TIER_RE.match(heading_text):
            flagged.append(heading_text)

    if not flagged:
        return []

    names = ", ".join(f'"{s}"' for s in flagged)
    return [LintResult(
        rule_id=19,
        severity=Severity.WARNING,
        message=(
            f"SKILL.md contains README-tier sections: {names}. "
            "These are human-facing — move to README.md to keep SKILL.md focused on agent workflow."
        ),
        file="SKILL.md",
    )]


# ---------------------------------------------------------------------------
# Rule 20: Triage workflow has no semantic review steps
# ---------------------------------------------------------------------------

# A triage workflow is present when SKILL.md has 3+ numbered step headings.
_TRIAGE_STEP_RE = re.compile(r"^###\s+Step\s+\d+", re.MULTILINE | re.IGNORECASE)

# Semantic review steps prompt the agent to apply judgment, not just run a
# command.  The canonical marker is "ask:" — as in "Read X and ask: does it...".
# This deliberately excludes steps that only contain code blocks or bullet-point
# action lists, which are purely mechanical.
_SEMANTIC_STEP_RE = re.compile(
    r"\bask\s*:"               # "Ask: ..."  (direct question prompt)
    r"|\bread\b.{0,80}\band\s+ask\b",  # "Read ... and ask:"
    re.IGNORECASE | re.DOTALL,
)

_TRIAGE_STEP_THRESHOLD = 3  # minimum steps before the rule fires


def check_triage_semantic_balance(skill_dir: Path) -> list[LintResult]:
    """Rule 20: A triage workflow should include at least one semantic review step.

    Automated commands cover structural signals; agent judgment is needed for
    semantic ones.  A workflow composed entirely of CLI commands will silently
    miss quality issues that no regex can reliably detect — the same failure
    mode that led to Rules 8, 12, 16, and 18 being removed from this linter.
    """
    text = _read_text(skill_dir / "SKILL.md")
    if text is None:
        return []

    body = _body_after_frontmatter(text)

    steps = _TRIAGE_STEP_RE.findall(body)
    if len(steps) < _TRIAGE_STEP_THRESHOLD:
        return []  # too few steps to constitute a meaningful triage workflow

    if _SEMANTIC_STEP_RE.search(body):
        return []  # at least one semantic review step present

    return [LintResult(
        rule_id=20,
        severity=Severity.INFO,
        message=(
            f"SKILL.md has {len(steps)} triage steps but none contain a semantic "
            "review prompt (e.g. 'Ask: does it…'). "
            "Automated steps cover structural signals; add at least one step where "
            "the agent applies judgment for signals that pattern-matching cannot "
            "reliably detect."
        ),
        file="SKILL.md",
    )]


_PEP723_BLOCK_RE = re.compile(r"^# /// script\s*$", re.MULTILINE)
_SHEBANG_RE = re.compile(r"^#!/")


def check_pep723_entry_points(skill_dir: Path) -> list[LintResult]:
    """Rule 21: Python entry-point scripts in scripts/ should declare deps via PEP 723.

    A shebang identifies a file as an executable entry point (not a module).
    Entry points that lack a `# /// script` block require a separate install step,
    making the skill non-self-contained — agents cannot invoke it with a single
    `uv run` without pre-installing dependencies.
    """
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir():
        return []

    violations: list[str] = []
    for py_file in sorted(scripts_dir.glob("*.py")):
        text = _read_text(py_file)
        if text is None or not _SHEBANG_RE.match(text):
            continue  # not an entry point — module files have no shebang
        if not _PEP723_BLOCK_RE.search(text):
            violations.append(py_file.name)

    if not violations:
        return []

    return [LintResult(
        rule_id=21,
        severity=Severity.WARNING,
        message=(
            f"Python entry-point script(s) in scripts/ lack PEP 723 inline dependency "
            f"metadata (# /// script block): {', '.join(violations)}. "
            "Declare dependencies inline so agents can invoke with `uv run` without a "
            "separate install step."
        ),
        file="scripts/",
    )]


def check_skill_isolation(skill_dir: Path) -> list[LintResult]:
    """Rule 17: skill files should be isolated from non-skill artifacts.

    When SKILL.md lives at the repo root, `npx skills add` installs the entire
    directory — including READMEs, LICENSE, test suites, and build artifacts
    that agents never need. Moving SKILL.md (and references/) into a skill/
    subdirectory limits installation to only what agents require.
    """
    if not (skill_dir / ".git").exists():
        return []  # not a repo root — already isolated or being tested directly

    found: list[str] = []
    for entry in sorted(skill_dir.iterdir()):
        name = entry.name
        if entry.is_dir() and name in _NON_SKILL_DIRS:
            found.append(f"{name}/")
        elif entry.is_file() and (
            name in _NON_SKILL_FILES
            or name.endswith(".lock")
        ):
            found.append(name)

    if not found:
        return []

    return [LintResult(
        rule_id=17,
        severity=Severity.INFO,
        message=(
            f"SKILL.md is at repo root alongside non-skill artifacts: "
            f"{', '.join(found)}. "
            "Move SKILL.md and skill-owned directories (references/, scripts/, assets/) "
            "into a skill/ subdirectory so `npx skills add` installs only what agents need."
        ),
    )]


# ---------------------------------------------------------------------------
# Rule 24: Plugin manifest validity
# ---------------------------------------------------------------------------

_REQUIRED_PLUGIN_KEYS = ("name", "version")


def check_plugin_manifest(plugin_root: Path) -> list[LintResult]:
    """Rule 24: `.claude-plugin/plugin.json` exists, parses, and declares required keys.

    Only fires when invoked with a plugin root (presence of the manifest is the
    trigger). For single-skill repos this rule is silent.
    """
    manifest_path = plugin_root / PLUGIN_MANIFEST_RELPATH
    if not manifest_path.is_file():
        return []  # not a plugin — single-skill rules apply instead

    text = _read_text(manifest_path)
    try:
        data = json.loads(text or "")
    except json.JSONDecodeError as exc:
        return [LintResult(
            rule_id=24,
            severity=Severity.ERROR,
            message=f".claude-plugin/plugin.json does not parse as JSON: {exc}.",
            file=str(PLUGIN_MANIFEST_RELPATH),
        )]

    if not isinstance(data, dict):
        return [LintResult(
            rule_id=24,
            severity=Severity.ERROR,
            message=".claude-plugin/plugin.json must be a JSON object.",
            file=str(PLUGIN_MANIFEST_RELPATH),
        )]

    missing = [k for k in _REQUIRED_PLUGIN_KEYS if not data.get(k)]
    if missing:
        return [LintResult(
            rule_id=24,
            severity=Severity.ERROR,
            message=(
                f".claude-plugin/plugin.json is missing required key(s): {', '.join(missing)}."
            ),
            file=str(PLUGIN_MANIFEST_RELPATH),
        )]
    return []


# ---------------------------------------------------------------------------
# Rule 25: Skill scripts importing local packages must be discoverable
# ---------------------------------------------------------------------------

# Imports the linter doesn't need to scrutinise: stdlib and a small whitelist
# of universally-available third-party packages that won't be local to the
# plugin (used as a sanity escape; everything else is verified explicitly).
_STDLIB = set(sys.stdlib_module_names) | {"_typeshed"}

_PEP723_FENCE_OPEN = re.compile(r"^# /// script\s*$", re.MULTILINE)
_PEP723_FENCE_CLOSE = re.compile(r"^# ///\s*$", re.MULTILINE)
_PEP723_DEPS_RE = re.compile(
    r"^# dependencies\s*=\s*\[(?P<body>.*?)^# \]\s*$",
    re.MULTILINE | re.DOTALL,
)
_PEP723_DEP_LINE_RE = re.compile(r'^#\s*"([^"]+)"', re.MULTILINE)


def _has_pep723_block(text: str) -> bool:
    """Return True if the script has a PEP 723 inline metadata block.

    We don't try to validate that the block's `dependencies` cover every
    imported name — distribution-name vs import-name mapping (pyyaml→yaml,
    beautifulsoup4→bs4, pillow→PIL, …) is impossible to do reliably without
    actually installing packages. The block's *presence* is the user's
    contract that this script declares its own deps; trust the analyst on
    the contents.
    """
    open_match = _PEP723_FENCE_OPEN.search(text)
    if not open_match:
        return False
    return _PEP723_FENCE_CLOSE.search(text, pos=open_match.end()) is not None


def _pyproject_dep_names(pyproject_path: Path) -> set[str]:
    """Return all top-level package names declared in pyproject.toml.

    Includes [project.dependencies], [tool.hatch.build.targets.wheel.packages],
    and the [project].name itself (so a plugin importing its own package passes).
    """
    text = _read_text(pyproject_path)
    if not text:
        return set()
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return set()

    names: set[str] = set()
    project = data.get("project", {}) or {}
    for entry in project.get("dependencies", []) or []:
        names.add(re.split(r"[<>=!~\[\s@]", entry, maxsplit=1)[0].strip().replace("-", "_"))
    if project.get("name"):
        names.add(str(project["name"]).replace("-", "_"))
    hatch_pkgs = (
        data.get("tool", {}).get("hatch", {}).get("build", {})
            .get("targets", {}).get("wheel", {}).get("packages", [])
    )
    names.update(str(p).replace("-", "_") for p in hatch_pkgs)
    return names


def _script_imports(text: str) -> set[str]:
    """Top-level package names imported by the script (best-effort AST parse)."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                names.add(node.module.split(".", 1)[0])
    return names


def check_local_package_deps(plugin_root: Path) -> list[LintResult]:
    """Rule 25: skill scripts importing non-stdlib code must declare a dep source.

    For each `skills/<name>/scripts/*.py`, parse top-level imports. If any are
    non-stdlib, the script must satisfy at least one of:
      - Has a PEP 723 inline metadata block (presence is the analyst's contract
        that runtime deps are declared inline).
      - All non-stdlib imports resolve to either:
          * a sibling directory at plugin root (sys.path-injection pattern), or
          * a name declared in plugin-root `pyproject.toml`.

    Otherwise the script will fail at runtime with `ModuleNotFoundError` when
    invoked from a fresh `uv run` environment.

    We deliberately do NOT validate that PEP 723 `dependencies` cover every
    individual import name — distribution-vs-import mapping (pyyaml→yaml,
    beautifulsoup4→bs4) is unreliable to do statically. PEP 723's *presence*
    is the contract; trust the user on the contents.
    """
    if not _is_plugin_root(plugin_root):
        return []  # only meaningful for plugin layouts

    skills_dir = plugin_root / "skills"
    if not skills_dir.is_dir():
        return []

    sibling_dirs = {
        p.name.replace("-", "_") for p in plugin_root.iterdir() if p.is_dir()
    }
    pyproject_names = _pyproject_dep_names(plugin_root / "pyproject.toml")

    results: list[LintResult] = []
    for skill_dir in sorted(skills_dir.iterdir()):
        scripts_dir = skill_dir / "scripts"
        if not scripts_dir.is_dir():
            continue
        for script in sorted(scripts_dir.glob("*.py")):
            text = _read_text(script)
            if not text:
                continue
            non_stdlib_imports = sorted(n for n in _script_imports(text) if n not in _STDLIB)
            if not non_stdlib_imports:
                continue

            # Pass condition A: PEP 723 block present (user has declared deps).
            if _has_pep723_block(text):
                continue

            # Pass condition B: every non-stdlib import resolves to a sibling
            # directory or is declared in plugin-root pyproject.toml.
            unresolved = [
                name for name in non_stdlib_imports
                if name.replace("-", "_") not in sibling_dirs
                and name.replace("-", "_") not in pyproject_names
            ]
            if not unresolved:
                continue

            rel = script.relative_to(plugin_root)
            results.append(LintResult(
                rule_id=25,
                severity=Severity.ERROR,
                message=(
                    f"Skill script `{rel}` imports {unresolved} with no dep source: "
                    f"no PEP 723 inline metadata, no plugin-root pyproject.toml entry, "
                    f"and no sibling directory at plugin root. The script will fail "
                    f"with ModuleNotFoundError under `uv run` from a fresh env."
                ),
                file=str(rel),
            ))
    return results
