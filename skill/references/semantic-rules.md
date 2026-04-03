# Semantic Rules Reference

Rules that require agent judgment rather than mechanical detection. Use these
examples during Step 5 (CSO signal), Step 7 (content overlap), and Step 8
(progressive disclosure) of the triage workflow.

---

## Rule 8 — Content overlap between SKILL.md and README

**Question:** Is the same information conveyed in different words across both files?

### Should flag

SKILL.md body and README contain the same substantive lines (even paraphrased):

```
# SKILL.md body
Run `skill-lint check .` to get the full picture.
Fix errors before warnings — Rule 1 blocks publishing.

# README.md (same content, slightly reworded)
Run `skill-lint check .` to get the full picture.
Fix errors before warnings — Rule 1 blocks publishing.
```

### Should not flag

Files share only incidental overlap (short lines, code snippets, headings):

```
# SKILL.md
## Triage Workflow
...

# README.md
## Usage
...
```

Overlap on lines shorter than ~20 characters, or on code blocks that must appear
in both, is expected and fine.

### Judgment call

SKILL.md should be agent-focused (triage workflow, rule table, references).
README should be human-focused (installation, starter prompts, badges).
Flag sections that duplicate *prose* between the two, not shared code examples.

---

## Rule 12 — CSO name is action-oriented

**Question:** Does the skill name read as an action (gerund preferred) rather than a noun?

### Should flag

```yaml
name: pdf-processor       # noun phrase
name: skill-creator       # noun phrase
name: code-reviewer       # noun phrase
```

### Should not flag

```yaml
name: processing-pdfs         # gerund
name: creating-skills         # gerund
name: condition-based-waiting # contains gerund segment
name: pdf                     # short well-known name — acceptable
name: commit                  # short well-known name — acceptable
name: debug                   # short well-known name — acceptable
```

### Judgment call

Apply common sense. A name like `pdf` or `commit` is universally understood as
an action in context and needs no gerund form. The goal is to prefer names that
read as "doing X" over names that read as "a thing that does X."

---

## Rule 16 — Dense or conditional sections belong in `references/`

**Question:** Would an agent look up this section reactively rather than read it upfront?

### Should flag

A step-conditional or phase heading whose body is dense enough to bulk up
the main workflow without being needed on every run:

```markdown
## Step 2 — Apply fixes

- detail line 0
- detail line 1
...
(35+ lines of specifics)
```

```markdown
## Phase 2 — Deploy

(35+ lines of deployment checklist)
```

```markdown
## After running the scan

(35+ lines of post-scan actions)
```

### Should not flag

A short step section that gives essential context upfront:

```markdown
## Step 2 — Fix Errors first

**Rule 1** (SKILL.md spec compliance) blocks publishing. Fix before anything else.
```

### Judgment call

Line count alone is not the criterion — the original Python threshold of 30 lines
was a proxy for "too much to absorb upfront." Use content density: a 35-line
section of dense checklists should move; a 35-line section of simple narrative
probably should not. Ask: "would an agent skip this on a normal run and only
read it when needed?"

---

## Rule 18 — Description is a single routing clause

**Question:** Does the `description` frontmatter function purely as a routing signal,
or has it been extended with elaboration?

### Should flag

Contains elaboration labels:

```yaml
description: Use when linting a skill. Triggers on: missing LICENSE, no CI.
description: Use when processing data. Use cases: CSV, JSON, XML.
description: Use when reviewing code. Checks: style, tests, security.
```

Multiple sentences:

```yaml
description: Use when linting a skill. It checks many things. Very useful.
description: Use when linting. It is helpful.
```

### Should not flag

Single routing clause, even with technical terms that contain punctuation:

```yaml
description: Use when validating a skill for publishing readiness.
description: Use when building X.Y.Z integrations.
description: Use when handling HTTP 4xx/5xx errors.
```

### Judgment call

Sentence-splitting on `.?!` is fragile — `X.Y.Z` and `4xx/5xx` are not sentence
boundaries. Read the description as a human would. The test is: does it say *when
to trigger the skill*, or does it start explaining *what the skill does*? The
former is correct; the latter belongs in the skill body.
