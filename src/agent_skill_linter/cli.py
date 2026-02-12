"""CLI: skill-lint check [--fix] [--format json]."""

from __future__ import annotations

import json
import sys

import click
from rich.console import Console
from rich.table import Table

from agent_skill_linter import __version__
from agent_skill_linter.linter import lint_skill
from agent_skill_linter.models import LintResult, Severity

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
        from agent_skill_linter.fixers import apply_fixes

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

    counts = {}
    for r in results:
        counts[r.severity] = counts.get(r.severity, 0) + 1
    summary = ", ".join(f"{v} {k.value}s" for k, v in counts.items())
    console.print(f"\n{summary}")
