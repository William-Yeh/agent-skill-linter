# Expected Layouts

The linter recognizes two layouts and switches mode automatically.

## Single skill (installed via `npx skills add`)

A well-structured skill repo separates agent-facing files (installed by `npx skills add`) from repo artifacts:

```
my-skill/
├── skill/               ← only this dir is installed by npx
│   ├── SKILL.md
│   ├── references/
│   │   └── fix-templates.md
│   └── scripts/         ← skill-invoked scripts (optional)
│       └── main.py
├── src/                 ← linter/library source (not installed)
├── tests/
├── README.md
├── LICENSE
├── pyproject.toml
└── .github/
    └── workflows/
```

The **lint target** is the `skill/` subdirectory (or repo root for older repos with no `skill/` dir).

## Plugin (installed via `/plugin install`)

A Claude Code plugin bundles multiple skills, optional commands/hooks/agents, and shared library code under one identity. Required marker: `.claude-plugin/plugin.json` at repo root.

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json                 ← required: name, version
├── skills/<name>/SKILL.md          ← one or more skills
├── <package_name>/                 ← optional shared Python code
├── commands/, agents/, hooks/      ← optional components
├── pyproject.toml                  ← optional; required if scripts import a
│                                     local package not declared via PEP 723
├── README.md, LICENSE
└── .github/workflows/
```

The **lint target** is the plugin root. The linter auto-detects via `.claude-plugin/plugin.json`, validates the manifest (Rule 24), checks each skill's script-dependency story (Rule 25), and runs the per-skill rule pack against every `skills/<name>/`. Plugin-root artifacts (README, LICENSE, CI) are checked once across all skills, not per skill.
