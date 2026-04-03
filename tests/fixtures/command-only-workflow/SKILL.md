---
name: command-only-workflow
description: Use when testing the triage balance rule.
metadata:
  author: Test Author
---

# Command-Only Workflow

A skill whose triage steps are all mechanical commands with no semantic review.

## Triage Workflow

### Step 1 — Run the linter

```bash
tool check .
```

### Step 2 — Auto-fix warnings

```bash
tool check . --fix
```

### Step 3 — Resolve remaining warnings manually

See the rule table below for guidance.
