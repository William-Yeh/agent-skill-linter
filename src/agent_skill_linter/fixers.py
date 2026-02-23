"""Auto-fix generators and templates."""

from __future__ import annotations

import re
import subprocess
from datetime import datetime
from pathlib import Path

import click
import yaml

from agent_skill_linter.models import LintResult

# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_FIXERS: dict[int, callable] = {}


def _fixer(rule_id: int):
    """Register a fixer function for a rule."""
    def decorator(fn):
        _FIXERS[rule_id] = fn
        return fn
    return decorator


def apply_fixes(path: str | Path, results: list[LintResult]) -> None:
    """Apply auto-fixes for all fixable results."""
    skill_dir = Path(path).resolve()
    fixable = [r for r in results if r.fixable]
    seen_rules: set[int] = set()

    for result in fixable:
        if result.rule_id in seen_rules:
            continue
        seen_rules.add(result.rule_id)
        fixer = _FIXERS.get(result.rule_id)
        if fixer:
            click.echo(f"  Fixing rule {result.rule_id}: {result.message}")
            fixer(skill_dir, result)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _detect_github_remote(skill_dir: Path) -> tuple[str, str] | None:
    """Try to detect OWNER/REPO from git remote."""
    try:
        url = subprocess.check_output(
            ["git", "-C", str(skill_dir), "remote", "get-url", "origin"],
            stderr=subprocess.DEVNULL, text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    # Handle SSH and HTTPS formats
    m = re.search(r"[:/]([^/]+)/([^/.]+?)(?:\.git)?$", url)
    if m:
        return m.group(1), m.group(2)
    return None


def _read_text(path: Path) -> str | None:
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return None


# ---------------------------------------------------------------------------
# Rule 2: LICENSE
# ---------------------------------------------------------------------------

_APACHE_TEMPLATE = """\
                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/

   Copyright {year} {author}

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

_MIT_TEMPLATE = """\
MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


@_fixer(2)
def fix_license(skill_dir: Path, result: LintResult) -> None:
    lic_path = skill_dir / "LICENSE"
    year = str(datetime.now().year)

    if lic_path.is_file():
        # Just update the year
        text = lic_path.read_text(encoding="utf-8")
        # Find any 4-digit year in copyright line and replace
        updated = re.sub(r"(Copyright\s.*?)(\d{4})", rf"\g<1>{year}", text)
        lic_path.write_text(updated, encoding="utf-8")
        return

    choice = click.prompt(
        "License type", type=click.Choice(["Apache-2.0", "MIT"]), default="Apache-2.0"
    )
    author = click.prompt("Copyright holder", default="<author>")

    template = _APACHE_TEMPLATE if choice == "Apache-2.0" else _MIT_TEMPLATE
    lic_path.write_text(template.format(year=year, author=author), encoding="utf-8")


# ---------------------------------------------------------------------------
# Rule 3: metadata.author
# ---------------------------------------------------------------------------

@_fixer(3)
def fix_author(skill_dir: Path, result: LintResult) -> None:
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    author = click.prompt("Author name for SKILL.md metadata.author")

    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return

    fm_text = m.group(1)
    data = yaml.safe_load(fm_text) or {}
    metadata = data.get("metadata", {}) or {}
    metadata["author"] = author
    data["metadata"] = metadata

    new_fm = yaml.dump(data, default_flow_style=False, sort_keys=False).strip()
    new_text = f"---\n{new_fm}\n---{text[m.end():]}"
    skill_md.write_text(new_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Rule 4: README badges
# ---------------------------------------------------------------------------

_BADGE_BLOCK = """\
[![CI](https://github.com/{owner}/{repo}/actions/workflows/ci.yml/badge.svg)]\
(https://github.com/{owner}/{repo}/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/{owner}/{repo})](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-blue)]\
(https://agentskills.io)
"""


@_fixer(4)
def fix_badges(skill_dir: Path, result: LintResult) -> None:
    readme_path = skill_dir / "README.md"
    remote = _detect_github_remote(skill_dir)

    if remote:
        owner, repo = remote
    else:
        owner = click.prompt("GitHub owner (for badges)", default="OWNER")
        repo = click.prompt("GitHub repo (for badges)", default="REPO")

    badge_text = _BADGE_BLOCK.format(owner=owner, repo=repo)

    if readme_path.is_file():
        text = readme_path.read_text(encoding="utf-8")
        # Insert after first heading, or at top
        m = re.match(r"(#[^\n]*\n)", text)
        if m:
            new_text = text[: m.end()] + "\n" + badge_text + "\n" + text[m.end():]
        else:
            new_text = badge_text + "\n" + text
    else:
        new_text = f"# {repo}\n\n{badge_text}\n"

    readme_path.write_text(new_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Rule 5: CI workflow
# ---------------------------------------------------------------------------

_CI_TEMPLATE = """\
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv run skill-lint check .

  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uvx --from skills-ref agentskills validate .
"""


@_fixer(5)
def fix_ci_workflow(skill_dir: Path, result: LintResult) -> None:
    wf_dir = skill_dir / ".github" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    ci_path = wf_dir / "ci.yml"
    if not ci_path.exists():
        ci_path.write_text(_CI_TEMPLATE, encoding="utf-8")


# ---------------------------------------------------------------------------
# Rule 6: Installation section
# ---------------------------------------------------------------------------

_INSTALL_SECTION = """
## Installation

### Recommended: `npx skills`

```bash
npx skills add {owner}/{repo}
```

### Manual installation

Copy the skill directory to your agent's skill folder:

| Agent | Directory |
|-------|-----------|
| Claude Code | `~/.claude/skills/` |
| Cursor | `.cursor/skills/` |
| Gemini CLI | `.gemini/skills/` |
| Amp | `.amp/skills/` |
| Roo Code | `.roo/skills/` |
| Copilot | `.github/skills/` |
"""


@_fixer(6)
def fix_installation_section(skill_dir: Path, result: LintResult) -> None:
    readme_path = skill_dir / "README.md"
    if not readme_path.is_file():
        return

    remote = _detect_github_remote(skill_dir)
    if remote:
        owner, repo = remote
    else:
        owner, repo = "OWNER", "REPO"

    text = readme_path.read_text(encoding="utf-8")
    section = _INSTALL_SECTION.format(owner=owner, repo=repo)
    readme_path.write_text(text.rstrip() + "\n" + section, encoding="utf-8")


# ---------------------------------------------------------------------------
# Rule 7: Usage section
# ---------------------------------------------------------------------------

_USAGE_SECTION = """
## Usage

After installing the skill, try these prompts with your agent:

- `TODO: Add a starter prompt here`
- `TODO: Add another starter prompt`

### CLI usage

You can also run the script directly:

```bash
TODO: skill-name command [options]
```
"""


@_fixer(7)
def fix_usage_section(skill_dir: Path, result: LintResult) -> None:
    readme_path = skill_dir / "README.md"
    if not readme_path.is_file():
        return

    text = readme_path.read_text(encoding="utf-8")
    readme_path.write_text(text.rstrip() + "\n" + _USAGE_SECTION, encoding="utf-8")
