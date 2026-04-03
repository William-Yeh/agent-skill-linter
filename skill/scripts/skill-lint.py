#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "skills-ref",
#   "click",
#   "pyyaml",
#   "rich",
# ]
# ///

"""skill-lint — check agent skills for spec compliance and publishing readiness."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

# This file is always the entry point, never imported as a library.
# Mutating sys.path here is intentional so sibling modules resolve correctly
# at runtime. conftest.py handles the equivalent setup for tests.
sys.path.insert(0, str(Path(__file__).parent))

import click
from rich.console import Console
from rich.table import Table

from linter import lint_skill
from models import LintResult, Severity

__version__ = "0.10.0"

SEVERITY_STYLE = {
    Severity.ERROR: "bold red",
    Severity.WARNING: "yellow",
    Severity.INFO: "dim",
}


@click.group()
@click.version_option(version=__version__, prog_name="skill-lint")
def main():
    """Lint agent skills for spec compliance and publishing readiness."""


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.option("--fix", is_flag=True, help="Auto-fix fixable issues.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def check(path: str, fix: bool, fmt: str):
    """Check a skill directory for issues."""
    results = lint_skill(path)

    if fix:
        from fixers import apply_fixes
        apply_fixes(path, results)
        results = lint_skill(path)

    if fmt == "json":
        _print_json(results)
    else:
        _print_table(results)

    has_errors = any(r.severity == Severity.ERROR for r in results)
    sys.exit(1 if has_errors else 0)


def _print_json(results: list[LintResult]):
    data = [
        {
            "rule": r.rule_id,
            "severity": r.severity.value,
            "message": r.message,
            "fixable": r.fixable,
            "file": r.file,
        }
        for r in results
    ]
    click.echo(json.dumps(data, indent=2))


def _print_table(results: list[LintResult]):
    console = Console()

    if not results:
        console.print("[bold green]All checks passed![/]")
        return

    table = Table(title="Lint Results", show_lines=False)
    table.add_column("Rule", style="bold", width=6)
    table.add_column("Severity", width=9)
    table.add_column("Message")
    table.add_column("Fix?", width=5)

    for r in sorted(results, key=lambda r: (r.severity.value, r.rule_id)):
        sev_style = SEVERITY_STYLE[r.severity]
        table.add_row(
            str(r.rule_id),
            f"[{sev_style}]{r.severity.value}[/]",
            r.message,
            "yes" if r.fixable else "",
        )
    console.print(table)

    counts = Counter(r.severity for r in results)
    summary = ", ".join(f"{v} {k.value}s" for k, v in counts.items())
    console.print(f"\n{summary}")


if __name__ == "__main__":
    main()
