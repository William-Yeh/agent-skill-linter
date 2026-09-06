# Agent Skill Linter

Checks agent skills for spec compliance and publishing readiness. This glossary
names the document categories and quality standards the rules talk about.

## Language

**Skill**:
A directory containing a `SKILL.md` plus optional `references/` and `scripts/`
that an agent loads to gain a capability.
_Avoid_: Plugin (that is a bundle of skills), tool

**Plugin**:
A repo marked by `.claude-plugin/plugin.json` that bundles one or more skills
with optional commands, hooks, and agents.
_Avoid_: Skill pack, bundle

**Agent-facing document**:
A file an agent reads to do its job: `SKILL.md` and anything under `references/`.
_Avoid_: Skill docs, internal docs

**Human-facing document**:
A file written for a person deciding whether and how to use the skill: the
README and any user guide (`USER_GUIDE.md`, `USAGE.md`, `GUIDE.md`,
`docs/guide.md`). Design docs and ADRs are not included.
_Avoid_: README-tier (use only for headings), user docs, public docs

**Plain prose**:
The writing standard for human-facing documents: leads with what the thing does
and who it is for, uses short active sentences, and carries no marketing fluff
or AI-flavored filler. Applies in whatever natural language the document uses.
_Avoid_: Readable, human-friendly, straightforward style

**Mechanical rule**:
A numbered check the Python linter runs by pattern matching, producing a
`LintResult`.
_Avoid_: Static rule, Python rule

**Semantic step**:
A numbered step in the triage workflow where the agent applies a judgment the
linter cannot make, guided by examples in `references/semantic-rules.md`.
_Avoid_: Semantic rule (that is the example entry, not the step), LLM check

**Reader**:
The person a human-facing document is written for: a developer who knows agent
skills but has never seen this project.
_Avoid_: User, audience, newcomer

**Sibling skill**:
Another skill maintained in the same umbrella repo, installable on its own,
whose capability this linter can invoke rather than reimplement.
_Avoid_: Dependency, upstream skill, plugin

**Delegated audit**:
A semantic step that hands a judgment to a sibling skill when that skill is
available to the agent, and falls back to an inline checklist when it is not.
_Avoid_: Shell-out, integration, external check
