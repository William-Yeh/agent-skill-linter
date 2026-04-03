"""Data models for lint results."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class LintResult:
    rule_id: int
    severity: Severity
    message: str
    fixable: bool = False
    file: str | None = None
