#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""Declares `pyyaml` via PEP 723 — Rule 25 must accept this."""

from __future__ import annotations

import yaml  # noqa: F401
